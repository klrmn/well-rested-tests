node['base']['python']['packages'].each do |pkg, version|
  python_pip pkg.to_s do
    version version
  end
end
