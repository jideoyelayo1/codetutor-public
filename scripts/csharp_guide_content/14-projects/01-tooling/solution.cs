// Directory.Packages.props
//   <Project>
//     <PropertyGroup><ManagePackageVersionsCentrally>true</ManagePackageVersionsCentrally></PropertyGroup>
//     <ItemGroup><PackageVersion Include="Serilog" Version="4.3.0" /></ItemGroup>
//   </Project>
// Project file:
//   <PackageReference Include="Serilog" />
Console.WriteLine("With central package management the version lives only in Directory.Packages.props, so every project uses the same one.");
