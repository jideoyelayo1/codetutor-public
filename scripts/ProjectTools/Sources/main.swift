import Foundation
import XcodeProj
import PathKit
let project = try XcodeProj(path: Path("CodingTeacher.xcodeproj"))
for package in project.pbxproj.projects.first!.remotePackages {
    if (package.repositoryURL ?? "").contains("swift-fsrs") {
        package.versionRequirement = .revision("4fbaf20184d62f82a9f44f343337c61a2c5483e9")
    } else if (package.repositoryURL ?? "").contains("TreeSitterLanguages") {
        package.versionRequirement = .exact("0.1.10")
    } else if (package.repositoryURL ?? "").contains("Runestone") {
        package.versionRequirement = .exact("0.5.2")
    }
}
try project.write(path: Path("CodingTeacher.xcodeproj"))
print("Pinned audited dependency revisions.")
// The installer links nativeTargets.first, whose order is unstable, so relink by target name.
let app = project.pbxproj.nativeTargets.first { $0.name == "CodingTeacher" }!
for target in project.pbxproj.nativeTargets {
    target.packageProductDependencies = []
    for phase in target.buildPhases.compactMap({ $0 as? PBXFrameworksBuildPhase }) { phase.files = [] }
}
let products: [(String, String)] = [("swift-fsrs", "FSRS"), ("Runestone", "Runestone")] + ["Python", "CPP", "CSharp", "Go", "JavaScript", "OCaml", "Rust"].map { ("TreeSitterLanguages", "TreeSitter\($0)Runestone") }
let phase = app.buildPhases.compactMap { $0 as? PBXFrameworksBuildPhase }.first!
for (repository, name) in products {
    let package = project.pbxproj.projects.first!.remotePackages.first { ($0.repositoryURL ?? "").hasSuffix(repository) }!
    let dependency = XCSwiftPackageProductDependency(productName: name, package: package)
    project.pbxproj.add(object: dependency)
    app.packageProductDependencies?.append(dependency)
    let file = PBXBuildFile(product: dependency)
    project.pbxproj.add(object: file)
    phase.files?.append(file)
}
try project.write(path: Path("CodingTeacher.xcodeproj"))
print("Linked all dependencies to the app target by name.")
for config in project.pbxproj.projects.first!.buildConfigurationList!.buildConfigurations where config.name == "Debug" {
    config.buildSettings["ONLY_ACTIVE_ARCH"] = "YES"
}
try project.write(path: Path("CodingTeacher.xcodeproj"))
for config in app.buildConfigurationList!.buildConfigurations {
    config.buildSettings["CODE_SIGN_ENTITLEMENTS[sdk=iphonesimulator*]"] = "Configuration/Simulator.entitlements"
    config.buildSettings["CODE_SIGN_IDENTITY[sdk=iphonesimulator*]"] = "-"
}
try project.write(path: Path("CodingTeacher.xcodeproj"))
print("Configured simulator-only ad hoc signing for app-local Keychain tests.")
for config in app.buildConfigurationList!.buildConfigurations {
    config.buildSettings["MARKETING_VERSION"] = "0.1.0"
    config.buildSettings["CURRENT_PROJECT_VERSION"] = "1"
    config.buildSettings["ASSETCATALOG_COMPILER_APPICON_NAME"] = "AppIcon"
}
try project.write(path: Path("CodingTeacher.xcodeproj"))
