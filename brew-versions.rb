require "formula_versions"

raise "Please `brew update` first" unless (HOMEBREW_REPOSITORY/".git").directory?
raise FormulaUnspecifiedError if ARGV.named.empty?

ARGV.formulae.each do |f|
  versions = FormulaVersions.new(f)
  path = versions.repository_path
  versions.each do |version, rev|
    print "#{Tty.white}#{version.to_s.ljust(8)}#{Tty.reset} "
    puts "git checkout #{rev} #{path}"
  end
end
