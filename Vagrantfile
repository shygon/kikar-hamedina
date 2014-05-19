# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "precise64"
  config.vm.box_url = "http://files.vagrantup.com/precise64.box"

  config.vm.network "private_network", ip: "192.168.100.100"
  config.vm.network :forwarded_port, guest: 8000, host: 8000

  config.vm.provision :shell, :inline => "apt-get update"

  config.vm.provision :shell, :inline => "apt-get install -y postgresql postgresql-contrib python-dev python-pip libpq-dev git-core build-essential"

  # Generate config files and initialize DB
  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      set -e

      # Create basic settings
      echo "# Auto generated code - do not edit
SECRET_KEY = '$(base64 /dev/urandom | head -c 50)'
" > /vagrant/kikar_hamedina/kikar_hamedina/settings/key.py

      # Create posresql 'admin' user
      sudo -u postgres psql -c "DROP DATABASE IF EXISTS kikar_hamedina"
      sudo -u postgres psql -c "DROP ROLE IF EXISTS admin"
      sudo -u postgres psql -c "CREATE USER admin WITH PASSWORD '123456'"
      sudo -u postgres psql -c "CREATE DATABASE kikar_hamedina TEMPLATE=template0 ENCODING='UTF8' LC_CTYPE='en_US.utf8' LC_COLLATE='en_US.UTF-8'"
    EOS
  end

  # pip requirements
  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      set -e
      # Do 2 pip tries as sometimes repositories fail to respond
      PIP="pip install -r /vagrant/requirements/vps.txt"
      $PIP || $PIP
    EOS
  end

  # Django setup
  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      set -e
      cd /vagrant/kikar_hamedina/
      python manage.py syncdb --noinput
      python manage.py dumpdata --indent=2 auth > initial_data.json
      for m in core persons mks links facebook_feeds video; do
        python manage.py migrate $m
      done
      for f in data_fixture_planet data_fixture_mks data_fixture_facebook_feeds; do
        python manage.py loaddata ${f}.json
      done
      # TODO: fix 'username is not a member of the user table.' error
      python manage.py fetchfeedproperties || true
      python manage.py fetchfeedstatuses
    EOS
  end

  config.vm.provision :shell do |shell|
    shell.inline = <<-EOS
      echo 'exec python /vagrant/kikar_hamedina/manage.py runserver 0.0.0.0:8000' > /etc/init/kikar.conf
      start kikar
    EOS
  end
end
