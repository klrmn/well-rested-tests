hostname = (ENV['VAGRANT_HOSTNAME'] || 'wrt-server')
ip_addr = (ENV['VAGRANT_IP'] || "192.168.8.80")
box_name = (ENV['VAGRANT_BOX'] || "trusty")
box_url = (ENV['VAGRANT_BOX_URL'] || "https://atlas.hashicorp.com/ubuntu/boxes/trusty64/versions/14.04/providers/virtualbox.box")
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
    config.vm.provision "chef_solo" do |chef|
        chef.cookbooks_path = [
            "well-rested-tests-server/cookbooks",
            "well-rested-tests-server/site-cookbooks"
        ]
        chef.add_recipe "base"
        chef.add_recipe "django"
        chef.add_recipe "python"
        chef.json = {
            "base" => {
                "python" => {
                    "packages" => [
                        "django",
                        "djangorestframework",
                        "django-filter",
                    ],
                }
            },
            "django" => {
                "python" => {
                    "install_method" => "package",
                    "gid" => "vagrant"
                },
                "app" => {
                    "project_home" => "/vagrant/well-rested-tests-server/wrt/",
                    "settings" => "wrt.settings",
                    "port" => "8080"
                },
                "log_dir" => "/var/log/",
            },
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