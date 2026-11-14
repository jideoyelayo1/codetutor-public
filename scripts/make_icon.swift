import AppKit
import Foundation
// Original vector artwork, rendered at the App Store icon size.
let size = 1024
let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8, samplesPerPixel: 3, hasAlpha: false, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
NSColor(calibratedRed: 0.047, green: 0.078, blue: 0.098, alpha: 1).setFill()
NSBezierPath(rect: NSRect(x: 0, y: 0, width: size, height: size)).fill()
let mint = NSColor(calibratedRed: 0.651, green: 0.851, blue: 0.765, alpha: 1)
func stroke(_ points: [NSPoint], width: CGFloat, color: NSColor) {
    let path=NSBezierPath(); path.move(to: points[0]); for p in points.dropFirst() { path.line(to:p) }
    path.lineWidth=width; path.lineCapStyle = .round; path.lineJoinStyle = .round; color.setStroke(); path.stroke()
}
let panel=NSBezierPath(roundedRect: NSRect(x:152,y:208,width:720,height:608),xRadius:72,yRadius:72)
NSColor(calibratedRed:0.084,green:0.129,blue:0.153,alpha:1).setFill(); panel.fill()
stroke([NSPoint(x:388,y:637),NSPoint(x:276,y:525),NSPoint(x:388,y:413)],width:38,color:mint)
stroke([NSPoint(x:636,y:637),NSPoint(x:748,y:525),NSPoint(x:636,y:413)],width:38,color:mint)
stroke([NSPoint(x:568,y:670),NSPoint(x:454,y:380)],width:34,color:mint)
stroke([NSPoint(x:306,y:288),NSPoint(x:512,y:255),NSPoint(x:718,y:288)],width:24,color:mint.withAlphaComponent(0.75))
NSGraphicsContext.restoreGraphicsState()
let folder=URL(fileURLWithPath: "CodingTeacher/Assets.xcassets/AppIcon.appiconset")
try FileManager.default.createDirectory(at:folder,withIntermediateDirectories:true)
try bitmap.representation(using:.png,properties:[:])!.write(to:folder.appendingPathComponent("AppIcon.png"))
try """
{"images":[{"filename":"AppIcon.png","idiom":"universal","platform":"ios","size":"1024x1024"}],"info":{"author":"xcode","version":1}}
""".write(to:folder.appendingPathComponent("Contents.json"),atomically:true,encoding:.utf8)
try "{\"info\":{\"author\":\"xcode\",\"version\":1}}".write(to:folder.deletingLastPathComponent().appendingPathComponent("Contents.json"),atomically:true,encoding:.utf8)
print("Created original app icon.")
