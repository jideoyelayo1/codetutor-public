import Foundation
let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
let project = root.appendingPathComponent("CodingTeacher.xcodeproj")
guard !FileManager.default.fileExists(atPath: project.path) else { print("Project already exists; preserving it."); exit(0) }
try FileManager.default.createDirectory(at: project, withIntermediateDirectories: true)
let pbx = """
// !$*UTF8*$!
{
 archiveVersion = 1;
 classes = {};
 objectVersion = 77;
 objects = {
 A00000000000000000000001 = { isa = PBXProject; attributes = { BuildIndependentTargetsInParallel = YES; LastUpgradeCheck = 2700; TargetAttributes = { A00000000000000000000005 = { CreatedOnToolsVersion = 27.0; }; A00000000000000000000006 = { CreatedOnToolsVersion = 27.0; TestTargetID = A00000000000000000000005; }; }; }; buildConfigurationList = A00000000000000000000010; compatibilityVersion = "Xcode 16.0"; developmentRegion = en; hasScannedForEncodings = 0; knownRegions = (en, Base); mainGroup = A00000000000000000000002; preferredProjectObjectVersion = 77; productRefGroup = A00000000000000000000003; projectDirPath = ""; projectRoot = ""; targets = (A00000000000000000000005, A00000000000000000000006); };
 A00000000000000000000002 = { isa = PBXGroup; children = (A00000000000000000000004, A00000000000000000000007, A00000000000000000000003); sourceTree = "<group>"; };
 A00000000000000000000003 = { isa = PBXGroup; children = (A00000000000000000000008, A00000000000000000000009); name = Products; sourceTree = "<group>"; };
 A00000000000000000000004 = { isa = PBXFileSystemSynchronizedRootGroup; path = CodingTeacher; sourceTree = "<group>"; };
 A00000000000000000000007 = { isa = PBXFileSystemSynchronizedRootGroup; path = CodingTeacherTests; sourceTree = "<group>"; };
 A00000000000000000000008 = { isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = CodingTeacher.app; sourceTree = BUILT_PRODUCTS_DIR; };
 A00000000000000000000009 = { isa = PBXFileReference; explicitFileType = wrapper.cfbundle; includeInIndex = 0; path = CodingTeacherTests.xctest; sourceTree = BUILT_PRODUCTS_DIR; };
 A00000000000000000000005 = { isa = PBXNativeTarget; buildConfigurationList = A00000000000000000000011; buildPhases = (A00000000000000000000020, A00000000000000000000021, A00000000000000000000022); buildRules = (); dependencies = (); fileSystemSynchronizedGroups = (A00000000000000000000004); name = CodingTeacher; packageProductDependencies = (); productName = CodingTeacher; productReference = A00000000000000000000008; productType = "com.apple.product-type.application"; };
 A00000000000000000000006 = { isa = PBXNativeTarget; buildConfigurationList = A00000000000000000000012; buildPhases = (A00000000000000000000023, A00000000000000000000024, A00000000000000000000025); buildRules = (); dependencies = (A00000000000000000000031); fileSystemSynchronizedGroups = (A00000000000000000000007); name = CodingTeacherTests; productName = CodingTeacherTests; productReference = A00000000000000000000009; productType = "com.apple.product-type.bundle.unit-test"; };
 A00000000000000000000020 = { isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000021 = { isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000022 = { isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000023 = { isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000024 = { isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000025 = { isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0; };
 A00000000000000000000030 = { isa = PBXContainerItemProxy; containerPortal = A00000000000000000000001; proxyType = 1; remoteGlobalIDString = A00000000000000000000005; remoteInfo = CodingTeacher; };
 A00000000000000000000031 = { isa = PBXTargetDependency; target = A00000000000000000000005; targetProxy = A00000000000000000000030; };
 A00000000000000000000010 = { isa = XCConfigurationList; buildConfigurations = (A00000000000000000000040, A00000000000000000000041); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; };
 A00000000000000000000011 = { isa = XCConfigurationList; buildConfigurations = (A00000000000000000000042, A00000000000000000000043); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; };
 A00000000000000000000012 = { isa = XCConfigurationList; buildConfigurations = (A00000000000000000000044, A00000000000000000000045); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release; };
 A00000000000000000000040 = { isa = XCBuildConfiguration; buildSettings = { CLANG_ENABLE_MODULES = YES; SDKROOT = iphoneos; IPHONEOS_DEPLOYMENT_TARGET = 18.0; SWIFT_VERSION = 5.0; SWIFT_OPTIMIZATION_LEVEL = "-Onone"; DEBUG_INFORMATION_FORMAT = dwarf; ENABLE_TESTABILITY = YES; }; name = Debug; };
 A00000000000000000000041 = { isa = XCBuildConfiguration; buildSettings = { CLANG_ENABLE_MODULES = YES; SDKROOT = iphoneos; IPHONEOS_DEPLOYMENT_TARGET = 18.0; SWIFT_VERSION = 5.0; SWIFT_COMPILATION_MODE = wholemodule; VALIDATE_PRODUCT = YES; }; name = Release; };
 A00000000000000000000042 = { isa = XCBuildConfiguration; buildSettings = { CODE_SIGN_STYLE = Automatic; GENERATE_INFOPLIST_FILE = YES; INFOPLIST_KEY_CFBundleDisplayName = "Coding Teacher"; INFOPLIST_KEY_UILaunchScreen_Generation = YES; INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES; INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES; INFOPLIST_KEY_UIRequiresFullScreen = NO; PRODUCT_BUNDLE_IDENTIFIER = com.jideoyelayo.CodingTeacher; PRODUCT_NAME = "$(TARGET_NAME)"; TARGETED_DEVICE_FAMILY = "1,2"; SWIFT_EMIT_LOC_STRINGS = YES; }; name = Debug; };
 A00000000000000000000043 = { isa = XCBuildConfiguration; buildSettings = { CODE_SIGN_STYLE = Automatic; GENERATE_INFOPLIST_FILE = YES; INFOPLIST_KEY_CFBundleDisplayName = "Coding Teacher"; INFOPLIST_KEY_UILaunchScreen_Generation = YES; INFOPLIST_KEY_UIApplicationSceneManifest_Generation = YES; INFOPLIST_KEY_UIApplicationSupportsIndirectInputEvents = YES; INFOPLIST_KEY_UIRequiresFullScreen = NO; PRODUCT_BUNDLE_IDENTIFIER = com.jideoyelayo.CodingTeacher; PRODUCT_NAME = "$(TARGET_NAME)"; TARGETED_DEVICE_FAMILY = "1,2"; SWIFT_EMIT_LOC_STRINGS = YES; }; name = Release; };
 A00000000000000000000044 = { isa = XCBuildConfiguration; buildSettings = { GENERATE_INFOPLIST_FILE = YES; PRODUCT_BUNDLE_IDENTIFIER = com.jideoyelayo.CodingTeacherTests; PRODUCT_NAME = "$(TARGET_NAME)"; TARGETED_DEVICE_FAMILY = "1,2"; TEST_HOST = "$(BUILT_PRODUCTS_DIR)/CodingTeacher.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/CodingTeacher"; BUNDLE_LOADER = "$(TEST_HOST)"; }; name = Debug; };
 A00000000000000000000045 = { isa = XCBuildConfiguration; buildSettings = { GENERATE_INFOPLIST_FILE = YES; PRODUCT_BUNDLE_IDENTIFIER = com.jideoyelayo.CodingTeacherTests; PRODUCT_NAME = "$(TARGET_NAME)"; TARGETED_DEVICE_FAMILY = "1,2"; TEST_HOST = "$(BUILT_PRODUCTS_DIR)/CodingTeacher.app/$(BUNDLE_EXECUTABLE_FOLDER_PATH)/CodingTeacher"; BUNDLE_LOADER = "$(TEST_HOST)"; }; name = Release; };
 };
 rootObject = A00000000000000000000001;
}
"""
try pbx.write(to: project.appendingPathComponent("project.pbxproj"), atomically: true, encoding: .utf8)
let schemes = project.appendingPathComponent("xcshareddata/xcschemes")
try FileManager.default.createDirectory(at: schemes, withIntermediateDirectories: true)
try """
<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="2700" version="1.3">
<BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="CodingTeacher.app" BlueprintName="CodingTeacher" ReferencedContainer="container:CodingTeacher.xcodeproj"/></BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000006" BuildableName="CodingTeacherTests.xctest" BlueprintName="CodingTeacherTests" ReferencedContainer="container:CodingTeacher.xcodeproj"/></TestableReference></Testables></TestAction>
<LaunchAction buildConfiguration="Debug" selectedDebuggerIdentifier="Xcode.DebuggerFoundation.Debugger.LLDB" selectedLauncherIdentifier="Xcode.IDEFoundation.Launcher.LLDB" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugServiceExtension="internal" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="CodingTeacher.app" BlueprintName="CodingTeacher" ReferencedContainer="container:CodingTeacher.xcodeproj"/></BuildableProductRunnable></LaunchAction>
<ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES" savedToolIdentifier="" useCustomWorkingDirectory="NO"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="CodingTeacher.app" BlueprintName="CodingTeacher" ReferencedContainer="container:CodingTeacher.xcodeproj"/></BuildableProductRunnable></ProfileAction>
<AnalyzeAction buildConfiguration="Debug"/><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>
</Scheme>
""".write(to: schemes.appendingPathComponent("CodingTeacher.xcscheme"), atomically: true, encoding: .utf8)
print("Created synchronized iOS app and test targets.")
