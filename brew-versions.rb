require "formula_versions"

raise "Please `brew update` first" unless (HOMEBREW_REPOSITORY/".git").directory?
raise FormulaUnspecifiedError if ARGV.named.empty?

class EnhancedFormulaVersions < FormulaVersions
  # Restores functionality dropped from FormulaVersions in https://github.com/Homebrew/homebrew/commit/6cff0acb3d65908ab49de70afceb39177969668b
  # Fixes rev_list - see comment https://github.com/jmchilton/linuxbrew/commit/62c12ec15ae6cbc18a26b0c26cf1a052cddca998

  def each
    versions = Set.new
    rev_list do |rev|
      version = version_at_revision(rev)
      next if version.nil?
      yield version, rev if versions.add?(version)
    end
  end

   def rev_list(branch="HEAD")
     repository.cd do
       Utils.popen_read("git", "rev-list", "--full-history", "--abbrev-commit", "--remove-empty", branch, "--", entry_name) do |io|
         yield io.readline.chomp until io.eof?
       end
     end
   end

  def version_at_revision(rev)
    formula_at_revision(rev) { |f| f.version }
  end

end


ARGV.formulae.each do |f|
  versions = EnhancedFormulaVersions.new(f)
  path = versions.repository
  versions.each do |version, rev|
    print "#{Tty.white}#{version.to_s.ljust(8)}#{Tty.reset} "
    puts "git checkout #{rev} #{path}"
  end
end
