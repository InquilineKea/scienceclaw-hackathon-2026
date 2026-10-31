// Original read-only pixel comparison using native system frameworks.
import Foundation
import ImageIO
import CoreGraphics
import CryptoKit
let args=CommandLine.arguments
let original=URL(fileURLWithPath:args[1]),published=URL(fileURLWithPath:args[2])
func digest(_ image:CGImage)->String{
 let w=image.width,h=image.height
 var pixels=[UInt8](repeating:0,count:w*h*4)
 pixels.withUnsafeMutableBytes{b in
  let c=CGContext(data:b.baseAddress,width:w,height:h,bitsPerComponent:8,bytesPerRow:w*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!
  c.draw(image,in:CGRect(x:0,y:0,width:w,height:h))
 }
 return SHA256.hash(data:Data(pixels)).map{String(format:"%02x",$0)}.joined()
}
var records=[[String:Any]]()
for url in try FileManager.default.contentsOfDirectory(at:original,includingPropertiesForKeys:nil).sorted(by:{$0.lastPathComponent<$1.lastPathComponent}) where ["gif","png"].contains(url.pathExtension){
 let a=CGImageSourceCreateWithURL(url as CFURL,nil)!,b=CGImageSourceCreateWithURL(published.appendingPathComponent(url.lastPathComponent) as CFURL,nil)!
 let n=CGImageSourceGetCount(a);precondition(n==CGImageSourceGetCount(b))
 if url.pathExtension=="gif"{precondition(n==65)}
 var equal=true
 for i in 0..<n{autoreleasepool{
  let ai=CGImageSourceCreateImageAtIndex(a,i,nil)!,bi=CGImageSourceCreateImageAtIndex(b,i,nil)!
  precondition(ai.width==1100 && ai.height==720 && bi.width==1100 && bi.height==720)
  equal = equal && digest(ai)==digest(bi)
 }}
 records.append(["file":url.lastPathComponent,"frames":n,"width":1100,"height":720,"all_decoded_pixels_equal":equal])
}
let result=try JSONSerialization.data(withJSONObject:records,options:[.prettyPrinted,.sortedKeys]);print(String(data:result,encoding:.utf8)!)
