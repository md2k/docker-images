#
# Ubuntu Dockerfile
#
# https://github.com/dockerfile/ubuntu
#

# Pull base image.
FROM ubuntu:14.04

MAINTAINER Yevgen Flerko md2k@md2k.net

# Mysql predefined passwrod, but can be overriden on container run
#ENV W3_DB_PASS xkThETQNM7D6Yf

# How to install deb from url
# URL='http://path.to/my.deb'; FILE=`mktemp`; wget "$URL" -qO $FILE && sudo dpkg -i $FILE; rm $FILE

# Install.
RUN \
  sed -i 's/# \(.*multiverse$\)/\1/g' /etc/apt/sources.list && \
  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y build-essential pwgen && \
  apt-get install -y software-properties-common && \
  apt-get install -y byobu curl git htop atop man unzip vim nano wget elinks strace mc

# Install sshd
RUN \
  apt-get install -y openssh-server && \
  mkdir /var/run/sshd && \
  echo 'root:screencast' | chpasswd && \
  sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Install Puppet
RUN \
  export PUPPET_REPO="https://apt.puppetlabs.com/puppetlabs-release-"`lsb_release -a | grep Codename | awk '{ print $2 }'`".deb" && \
  FILE=`mktemp`; wget "$PUPPET_REPO" -qO $FILE && sudo dpkg -i $FILE; rm -f $FILE && \
  apt-get update && \
  apt-get install -y puppet facter

# Install docker for use as client to HOST Docer API
RUN apt-get install -y docker.io

# TODO:
# Temporary workaround when we link external puppet source
# for production we want do this by fetching data from git
RUN \
  rm -rf /etc/puppet && \
  ln -s /media/Puppet/puppet-w3/ /etc/puppet

# Clean Up TODO:
RUN rm -rf /var/lib/apt/lists/*

# Set File/Dir  permissions
#RUN chown -R www-data:www-data /usr/share/nginx/

# Install pip and template engine
#RUN pip install pystache

## Set Listening ports which will be availible only for linked containers and not externally
#EXPOSE 80 3306

# Add files.
ADD root/.bashrc /root/.bashrc
ADD root/.bash_aliases /root/.bash_aliases
ADD root/.gitconfig /root/.gitconfig
ADD root/.scripts /root/.scripts
ADD root/.config /root/.config
ADD run.sh /root/run.sh
RUN chmod +x /root/run.sh

# Set environment variables.
ENV HOME /root

# Define working directory.
WORKDIR /

# Define default command.
CMD /root/run.sh
