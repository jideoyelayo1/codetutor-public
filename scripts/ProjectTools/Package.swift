// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "ProjectTools", platforms: [.macOS(.v13)], dependencies: [.package(url: "https://github.com/tuist/XcodeProj.git", exact: "8.27.7")], targets: [.executableTarget(name: "ProjectTools", dependencies: ["XcodeProj"])])
