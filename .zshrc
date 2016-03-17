# Path to your oh-my-zsh installation.
export ZSH=/home/francois/.oh-my-zsh

# Set name of the theme to load.
# Look in ~/.oh-my-zsh/themes/
# Optionally, if you set this to "random", it'll load a random theme each
# time that oh-my-zsh is loaded.
ZSH_THEME="robbyrussell"

# Uncomment the following line to use case-sensitive completion.
# CASE_SENSITIVE="true"

# Uncomment the following line to use hyphen-insensitive completion. Case
# sensitive completion must be off. _ and - will be interchangeable.
# HYPHEN_INSENSITIVE="true"

# Uncomment the following line to disable bi-weekly auto-update checks.
# DISABLE_AUTO_UPDATE="true"

# Uncomment the following line to change how often to auto-update (in days).
# export UPDATE_ZSH_DAYS=13

# Uncomment the following line to disable colors in ls.
# DISABLE_LS_COLORS="true"

# Uncomment the following line to disable auto-setting terminal title.
# DISABLE_AUTO_TITLE="true"

# Uncomment the following line to enable command auto-correction.
# ENABLE_CORRECTION="true"

# Uncomment the following line to display red dots whilst waiting for completion.
# COMPLETION_WAITING_DOTS="true"

# Uncomment the following line if you want to disable marking untracked files
# under VCS as dirty. This makes repository status check for large repositories
# much, much faster.
# DISABLE_UNTRACKED_FILES_DIRTY="true"

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# The optional three formats: "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load? (plugins can be found in ~/.oh-my-zsh/plugins/*)
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(git)

# User configuration

export PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/home/francois/.npm-packages/bin"
# export MANPATH="/usr/local/man:$MANPATH"

source $ZSH/oh-my-zsh.sh

# You may need to manually set your language environment
# export LANG=en_US.UTF-8

# Preferred editor for local and remote sessions
# if [[ -n $SSH_CONNECTION ]]; then
#   export EDITOR='vim'
# else
#   export EDITOR='mvim'
# fi

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# ssh
# export SSH_KEY_PATH="~/.ssh/dsa_id"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"
alias zshrc="vim ~/.zshrc"
alias cdback="cd ~/Code/back-web"
alias cdfront="cd ~/Code/front-web"
alias ls="ls -lArth"
# Git

alias gfrp="git fetch upstream; git rebase upstream/master; git push origin master"
alias hc="bastion lrqhc"

# Clean Docker Volumes
alias dcleandry="curl -sS https://raw.githubusercontent.com/chadoe/docker-cleanup-volumes/master/docker-cleanup-volumes.sh | sudo bash /dev/stdin --dry-run"
alias dclean="curl -sS https://raw.githubusercontent.com/chadoe/docker-cleanup-volumes/master/docker-cleanup-volumes.sh | sudo bash"
alias cclean="dclean"

# Docker and Docker-compose
alias compose="docker-compose"
alias dsetup="compose run --rm web scripts/setup"
alias csetup="dsetup"
alias switchfixtures="docker-compose run --rm web switch_db fixtures"
alias switchdump="docker-compose run --rm web switch_db dump"
alias ddump="compose run --rm web scripts/importdump/import_daily_dump.sh"
alias cdump="ddump"
alias composeip="compose ps -q | xargs docker inspect --format '{{ .Name }} - {{ .NetworkSettings.IPAddress }}'"
alias dockerip="composeip"
alias ls="ls -lArth"
alias dconsole="compose run --rm web php /var/www/app/api/console"
alias dant="docker-compose run --rm web ant -f build/build.xml"
function dbash {
    docker exec -it "$1" bash;
}
function dunit {
    if [ -z $1 ]; then
    echo "Usage: dunit DIRECTORY"
      return 1
    fi

    compose run --rm web php app/api/vendor/bin/phpunit --color "$1";
}
function dunitdox {
    if [ -z $1 ]; then
    echo "Usage: dunit DIRECTORY"
      return 1
    fi

    compose run --rm web php app/api/vendor/bin/phpunit --color --testdox "$1";
}
function everyplace {
    if [ -z "$3" ]
    then
        echo "Usage: $FUNCNAME SEARCH_STRING REPLACE_STRING DIRECTORY";
        return 1;
    fi

    #grep -rl $1 $3 | xargs sed -ri "s/$1/$2/g"
    ag -l $1 $3 | xargs sed -ri "s/$1/$2/g"
}
function dbehat {

    if [ -z $1 ]; then
    echo "Usage: dbehat api|admin"
      return 1
    fi

    APPLICATION=$1
    if [[ x${APPLICATION} != xapi ]] &&
       [[ x${APPLICATION} != xadmin ]]
    then
       printf -- "$APPLICATION is not a valid application !\n"
       echo "Usage: run-behat api|admin"
       return 1
    fi
    shift
    docker-compose run --rm web app/$APPLICATION/vendor/bin/behat -c app/$APPLICATION/behat.yml $@

}
# bastion lrqhc
function bastion() {
 if [ -z $1 ]; then
  echo "Usage: bastion [host]"
  return 1
 fi
 ssh -t sshgate@89.31.147.28 -p 2223 $1
}

function lrqdo-token() {
    docker exec $(docker-compose ps -q web) php app/api/console lrqdo:oauth-server:token:generate $1 |
    grep 'Access token' |
    awk '{print $3}'
}

function open-profiler() {
    grep X-Debug-Token-Link | awk '{print "http://localhost:8080"$2"?panel=db"}' | xargs google-chrome
}

function lrqdo-profile() {
    URL="$1"
    TOKEN=$(lrqdo-token "$2")
    http --headers "http://localhost:8080$URL?access_token=$TOKEN" | open-profiler
}
function child-pid() {
 if [[ x"" = x"$@" ]]; then
  return 0
 else
  echo $@
  _LIST_PID=$(echo $@ | sed -e 's/ /,/g')
  child-pid $(pgrep -P ${_LIST_PID})
 fi
}

function docker-ps() {
 ps fu --ppid $(child-pid $(pidof docker))
}
function lrqdo-http() {
    URL="$1"
    TOKEN=$(lrqdo-token "$2")
    http "http://localhost:8080$URL?access_token=$TOKEN"
}

