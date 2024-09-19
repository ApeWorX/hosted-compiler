import vvm

installed_versions = vvm.get_installed_vyper_versions()
installable_versions = vvm.get_installable_vyper_versions()

for version in installable_versions:
    version_str = str(version.major) + "." + str(version.minor) + "." + str(version.micro)
    if version not in installed_versions:
        if version_str == "0.3.8":
            print("Skipping Broken version: " + version_str)

        elif version.is_prerelease is True:
            print("Skipping Uninstallable prerelease:" + version_str + str(version.pre))
        else:
            print("Installing version: " + version_str)
            vvm.install_vyper(version)
