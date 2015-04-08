include_recipe 'apt'
include_recipe "python"
include_recipe "python::#{node['python']['install_method']}"
include_recipe "python::pip"

include_recipe "base::packages"
include_recipe "base::python"
