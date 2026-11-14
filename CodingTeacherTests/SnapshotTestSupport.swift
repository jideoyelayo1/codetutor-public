import XCTest
import UIKit

/// Keep compressed screenshot data, releasing the decoded raster before an async test suspends.
@MainActor func makePNGTestAttachment(named name: String, render: () -> UIImage) throws -> XCTAttachment {
    weak var weakImage: UIImage?
    let attachment = try autoreleasepool { () throws -> XCTAttachment in
        let image = render()
        weakImage = image
        let data = try XCTUnwrap(image.pngData(), "Could not encode screenshot: \(name)")
        return XCTAttachment(data: data, uniformTypeIdentifier: "public.png")
    }
    XCTAssertNil(weakImage, "Decoded screenshot retained after PNG encoding: \(name)")
    attachment.name = name
    attachment.lifetime = .keepAlways
    return attachment
}
