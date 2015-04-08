log 'creating log directory'

directory node['django']['log_dir'] do
  owner "root"
  group "root"
  mode 00644
  action :create
end
