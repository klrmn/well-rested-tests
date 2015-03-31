hostname = (ENV['VAGRANT_HOSTNAME'] || 'wrt-server')
ip_addr = (ENV['VAGRANT_IP'] || "192.168.8.80")
box_name = (ENV['VAGRANT_BOX'] || "trusty")
box_url =  (ENV['VAGRANT_BOX'] || "https://atlas.hashicorp.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box")
current_datetime = Time.now.strftime("%Y%m%d-%H%M%S")

Vagrant.configure("2") do |global_config|
  global_config.ssh.forward_agent = true
  global_config.vm.define hostname do |config|
    if Gem::Version.new(Vagrant::VERSION) >= Gem::Version.new('1.5.0')
       config.ssh.insert_key = false
    end
    if (ENV['VAGRANT_GUI'] || false)
            vb.gui = true
    end
    # http://www.maigfrga.ntweb.co/entorno-de-desarrollo-vagrant-con-django-y-ubuntu/
    config.omnibus.chef_version = :latest
    config.librarian_chef.cheffile_dir = 'well-rested-tests-server/django-vagrant-chef'
    config.vm.provision "chef_solo" do |chef|
      chef.cookbooks_path = [
        "well-rested-tests-server/django-vagrant-chef/cookbooks",
        "well-rested-tests-server/django-vagrant-chef/site-cookbooks"
      ]
      chef.roles_path = "well-rested-tests-server/django-vagrant-chef/roles"
      chef.data_bags_path = "well-rested-tests-server/django-vagrant-chef/data_bags"
      chef.add_role('django')
      chef.json = {
        "postgresql" => {
            "password" => {
                "postgres" => "md58a2abbe42d6c5bb2181ac0c2fcefad91"
            }
        },
        "python" => {
            "install_method" => "package",
            "venv_dir" => "/svr/env/",
        },
        "django" => {
            "python" => {
                "packages" => [
                    "psycopg2",
                    "django",
                    "django-rest-framework"
                ],
            },
            "app" => {
                "project_home" => "/vagrant/well-rested-tests-server",
                "settings" => "project.settings",
                "port" => "8080"
            },
        },
        "supervisor" => {
            "inet_username" => "vagrant",
            "inet_password" => "vagrant"
        }
      }
    end
    config.vm.hostname = hostname
    config.vm.box = box_name
    config.vm.box_url = box_url
    config.vm.network :private_network, ip: ip_addr
    config.vm.provider :virtualbox do |vb|
    vb.name = "vagrant-#{hostname}-#{current_datetime}"
    vb.customize ["modifyvm", :id, "--memory", 3072]
    vb.customize ["modifyvm", :id, "--cpus", 2]
  end
end
end

