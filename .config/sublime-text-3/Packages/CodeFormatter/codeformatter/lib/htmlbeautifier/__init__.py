from __future__ import print_function
import sys
import re
import sublime
try:
 	# Python 3
	from .__version__ import __version__
except (ValueError):
 	# Python 2
	from __version__ import __version__

class BeautifierOptions:
	def __init__(self):
		self.indent_size = 4
		self.indent_char = ' '
		self.indent_with_tabs = False
		self.expand_tags = False
		self.expand_javascript = False
		self.minimum_attribute_count = 2
		self.first_attribute_on_new_line = False
		self.reduce_empty_tags = False
		self.exception_on_tag_mismatch = False
		self.custom_singletons = ''

	def __repr__(self):
		return """indent_size = %d
indent_char = [%s]
indent_with_tabs = [%s]
expand_tags = [%s]
expand_javascript = [%s]
minimum_attribute_count = %d
first_attribute_on_new_line = [%s]
reduce_empty_tags = [%s]
exception_on_tag_mismatch = [%s]
custom_singletons = [%s]""" % (self.indent_size, self.indent_char, self.indent_with_tabs, self.expand_tags, self.expand_javascript, self.minimum_attribute_count, self.first_attribute_on_new_line, self.reduce_empty_tags, self.exception_on_tag_mismatch, self.custom_singletons)

def default_options():
	return BeautifierOptions()

def beautify(string, opts=default_options()):
	b = Beautifier(string, opts)
	return b.beautify()

def beautify_file(file_name, opts=default_options()):
	if file_name == '-':  # stdin
		stream = sys.stdin
	else:
		stream = open(file_name)
	content = ''.join(stream.readlines())
	b = Beautifier(content, opts)
	return b.beautify()

def usage(stream=sys.stdout):
	print("htmlbeautifier.py@" + __version__ + "\nHTML beautifier (http://jsbeautifier.org/)\n", file=stream)
	return stream == sys.stderr
	if stream == sys.stderr: return 1
	else: return 0

class Beautifier:
	def __init__(self, source_text, opts=default_options()):
		self.source_text = source_text
		self.opts = opts
		self.exception_on_tag_mismatch = opts.exception_on_tag_mismatch
		self.expand_tags = opts.expand_tags
		self.expand_javascript = opts.expand_javascript
		self.minimum_attribute_count = opts.minimum_attribute_count
		self.first_attribute_on_new_line = opts.first_attribute_on_new_line
		self.reduce_empty_tags = opts.reduce_empty_tags
		self.indent_size = opts.indent_size
		self.indent_char = opts.indent_char
		self.indent_with_tabs = opts.indent_with_tabs
		if self.indent_with_tabs:
			self.indent_char = "\t"
			self.indent_size = 1
			self.tab_size = sublime.load_settings('Preferences.sublime-settings').get('tab_size',4)
		self.indent_level = 0
		# These are the tags that are currently defined as being void by the HTML5 spec, and should be self-closing (a.k.a. singletons)
		self.singletons = r'<(area|base|br|col|command|embed|hr|img|input|keygen|link|meta|param|source|track|wbr<%= custom %>)([^>]*)>'
		if not opts.custom_singletons == '':
			self.singletons = re.sub(r'<%= custom %>','|' + opts.custom_singletons,self.singletons)
		else:
			self.singletons = re.sub(r'<%= custom %>','',self.singletons)

	def remove_newlines(self,str):
		return re.sub(r'\n\s*',r'',str.group(1))

	def expand_tag(self,str):
		_str = str.group(0) # cache the original string in a variable for faster access
		s = re.findall(r'([\w\-]+(?:=(?:"[^"]*"|\'[^\']*\'))?)',_str)
		# If the tag has fewer than "minimum_attribute_count" attributes, leave it alone
		if len(s) <= self.minimum_attribute_count: return _str
		tagEnd = re.search(r'/?>$',_str)
		if not tagEnd == None: s += [tagEnd.group(0)] # Append the end of the tag to the array of attributes
		tag = '<' + s[0] # The '<' at the beginning of a tag is not included in the regex match
		indent = len(tag) + 1 # include the space after the tag name, this is not included in the regex
		s = s[1:] # pop the tag name off of the attribute array - we don't need it any more
		# Calculate how much to indent each line
		if self.first_attribute_on_new_line: # If we're putting all the attributes on their own line, only use 1 indentation unit
			if self.indent_with_tabs:
				indent = 0
				extra_tabs = 1
			else:
				indent = self.indent_size
				extra_tabs = 0
		else: # Otherwise, align the attributes with the beginning of the first attribute after the tag name
			if self.indent_with_tabs:
				extra_tabs = int(indent / self.tab_size)
				indent = indent % self.tab_size
			else:
				extra_tabs = 0
			tag += ' ' + s[0]
			s = s[1:] # Go ahead and pop the first attribute off the array so that we don't duplicate it in the loop below
		# For each attribute in the list, append a newline and indentation followed by the attribute (or the end of the tag)
		for l in s:
			tag += '\n' + (((self.indent_level * self.indent_size) + extra_tabs) * self.indent_char) + (indent * ' ') + l
		return tag

	def beautify(self):
		beautiful = ''
		raw = self.source_text

		# Replace single-line javascript comments with block comments so that expansion of the elements inside doesn't
		# become un-commented, ignoring commented CDATA tags
		if self.expand_javascript:
			raw = re.sub(r'(?<=\s)//(?!<!\[CDATA\[|\]\]>)(.+)\n',r'/*\1*/\n',raw)
			raw = re.sub(r';+',r';',raw)

		# Add newlines before/after tags (excluding CDATA). This separates single-line HTML comments into 3 lines as well
		raw = re.sub(r'(<[^! ]|(?<!/\*|//)\]\]>|(?<!<!\[endif\])-->)',r'\n\1',raw)
		raw = re.sub(r'(>|(?<!/\*|//)<!\[CDATA\[|<!--(?!\[if .+?\]>))',r'\1\n',raw)

		# Add newlines before=after javascript braces/switch cases/comments
		if self.expand_javascript:
			raw = re.sub(r'(\}|\*/)',r'\n\1',raw)
			raw = re.sub(r'(\{|/\*|(?<!\();(?!\))|(?:case [^:]+|default):)',r'\1\n',raw)
			raw = re.sub(r'\[(?!(?:if .+?\]>|endif\]-->))([^\]]+)\]',r'[\n\1\n]',raw)# Split javascript array entries onto new lines
			raw = re.sub(r'(\[[^\[\]]{0,10}\])',self.remove_newlines,raw)# Fix javascript regex that was broken by the previous regex replace
			raw = re.sub(r',(?!;$)([^:;\{]+:[^,])',r',\n\1',raw)		# Split javascript object entries onto new lines
			raw = re.sub(r'({[^\{}]{0,10}})',self.remove_newlines,raw)# Fix javascript regex that was broken by the previous regex replace
			raw = re.sub(r'((for|while)\s+?(\([^\)]+\))\s+?\{)',self.remove_newlines,raw)	# Put all the content of a loop def on the same line
			raw = re.sub(r'\},\s*?\{',r'},\n{',raw)
			# Fix CSS that will have been expanded by this option as well so that new CSS rulesets begin on their own line
			raw = re.sub(r'\}(.*?)(\{|;)',r'}\n\1\2',raw)
			# Fix AngularJS/Blade/etc brace ({{}}) templates that will have been broken into multiple lines
			raw = re.sub(r'(\{{2,})(.*?)(\}{2,})',r'\1 \2 \3',re.sub(r'(\{(?:\s*\{)+[\s\S]*?\}(?:\s*\})+)',self.remove_newlines,raw))

		raw = re.sub(r'("[^"]*")',self.remove_newlines,raw)				# Put all content between double-quote marks back on the same line
		raw = re.sub(self.singletons,r'<\1\2/>',raw)							# Replace all singleton tags with /-delimited tags (XHTML style)
		raw = raw.replace('//>','/>')															# Fix the singleton tags if they were already /-delimited
		raw = re.sub(r'\n{2,}',r'\n',raw)													# Replace multiple newlines with just one

		for l in re.split('\n',raw):
			l = l.strip()																						# Trim whitespace from the line
			if l == '' or l == ';': continue												# If the line has no content (HTML or JavaScript), skip

			# If the line starts with </, or an end CDATA/block comment tag, reduce indentation
			if re.match(r'</|]]>|(?:<!\[endif\])?-->',l): self.indent_level -= 1
			# If the line starts with }, a switch case, or the end of a block comment, reduce indentation
			if self.expand_javascript and re.match(r'\}|\]|(?:case [^:]+|default):|\*/',l): self.indent_level -= 1

			beautiful += (self.indent_char * self.indent_level * self.indent_size)
			if self.expand_tags:
				beautiful += re.sub(r'^<.*>$',self.expand_tag,l)
				# beautiful += re.sub(r'(<[^/!][^>]+>)',self.expand_tag,l)
			else:
				beautiful += l
			beautiful += '\n'

			if re.search(self.singletons,l): pass										# If the tag is a singleton, indentation stays the same
			else:
				# If the line starts with a begin CDATA/block comment tag or a tag, indent the next line
				if re.match(r'<!--|<!\[CDATA\[|<[^/?! ]',l): self.indent_level += 1
				# If the line starts with a block comment, switch case, or ends with {, indent the next line}
				if self.expand_javascript:
					if re.match(r'/\*|(?:case [^:]+|default):',l) or re.search(r'(?:\{|\[)$',l): self.indent_level += 1

		# If the end of the document is not at the same indentation as the beginning, the tags aren't matched
		if not self.indent_level == 0 and self.exception_on_tag_mismatch:
			raise Exception("Mismatched tags")

		# Put all matched start/end tags with no content between them on the same line and return
		if self.reduce_empty_tags:
			beautiful = re.sub(r'<([\w\-]+)([^>]*)>\s+</\1>',r'<\1\2></\1>',beautiful)

		# Put all single-line comments back on a single line - I separated them out earlier for simplicity's sake
		beautiful = re.sub(r'<!--\n\s+(.+)\n\s+-->',r'<!-- \1 -->',beautiful)

		return beautiful
