# -*- mode: ruby -*-
# vi: set ft=ruby :

# All Vagrant configuration is done below. The "2" in Vagrant.configure
# configures the configuration version (we support older styles for
# backwards compatibility). Please don't change it unless you know what
# you're doing.
Vagrant.configure("2") do |config|
  # The most common configuration options are documented and commented below.
  # For a complete reference, please see the online documentation at
  # https://docs.vagrantup.com.

  # config.ssh.password = "vagrant"
  # config.ssh.keys_only = false

  # Every Vagrant development environment requires a box. You can search for
  # boxes at https://atlas.hashicorp.com/search.
  config.vm.box = "ubuntu/xenial64"

  # Disable automatic box update checking. If you disable this, then
  # boxes will only be checked for updates when the user runs
  # `vagrant box outdated`. This is not recommended.
  # config.vm.box_check_update = false

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  config.vm.network "forwarded_port", guest: 8000, host: 8000, host_ip: "127.0.0.1"

  # Create a private network, which allows host-only access to the machine
  # using a specific IP.
  # config.vm.network "private_network", ip: "192.168.33.10"

  # Create a public network, which generally matched to bridged network.
  # Bridged networks make the machine appear as another physical device on
  # your network.
  # config.vm.network "public_network"

  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder ".", "/vagrant"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # Example for VirtualBox:
  #
  config.vm.provider "virtualbox" do |vb|
  #   # Display the VirtualBox GUI when booting the machine
  #   vb.gui = true
  #
  #   # Customize the amount of memory on the VM:
    vb.memory = "512"
  end
  #
  # View the documentation for the provider you are using for more
  # information on available options.

  # Define a Vagrant Push strategy for pushing to Atlas. Other push strategies
  # such as FTP and Heroku are also available. See the documentation at
  # https://docs.vagrantup.com/v2/push/atlas.html for more information.
  # config.push.define "atlas" do |push|
  #   push.app = "YOUR_ATLAS_USERNAME/YOUR_APPLICATION_NAME"
  # end

  # Enable provisioning with a shell script. Additional provisioners such as
  # Puppet, Chef, Ansible, Salt, and Docker are also available. Please see the
  # documentation for more information about their specific syntax and use.
  config.vm.provision "shell", inline: <<-SHELL, privileged: false
#    echo "ubuntu:ubuntu" | sudo chpasswd

    sudo apt-get update
    sudo apt-get install -y postgresql libpq-dev
    sudo apt-get install -y libjpeg-dev libfreetype6-dev
    sudo ln -s /usr/include/freetype2 /usr/include/freetype
    sudo apt-get install -y python2.7 python-pip python-pip python-virtualenv gettext

    sudo -upostgres psql -c "create user ubuntu password 'ubuntu'"
    sudo -upostgres psql -c "alter user ubuntu with superuser"
    sudo -upostgres psql -c "create database boarddocuments_db1 owner ubuntu"

    echo "host    all              ubuntu          127.0.0.1/0             md5" | sudo tee --append /etc/postgresql/9.5/main/pg_hba.conf
    sudo service postgresql reload

    echo '. env/bin/activate' >> ~/.bashrc
    echo 'cd /vagrant' >> ~/.bashrc

    virtualenv env
    source env/bin/activate
    pip install -r /vagrant/requirements-dev.txt

    cd /vagrant
    if [ ! -f settings/local.py ]; then
        cp settings/local.py.example settings/local.py
        sed -i "s/'USER': ''/'USER': 'ubuntu'/" settings/local.py
    fi

    python manage.py makemigrations --settings settings.local
    python manage.py migrate --settings settings.local

    python manage.py loaddata initial_data
    python manage.py loaddata flatpages

    # Use to run server:
    # python manage.py runserver 0.0.0.0:8000 --settings settings.local
  SHELL
end
