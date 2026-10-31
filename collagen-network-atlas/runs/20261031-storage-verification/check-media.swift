import Foundation
import ImageIO
let directory=CommandLine.arguments.count>1 ? CommandLine.arguments[1]:"figures"
var rows=[[String:Any]]()
for url in try FileManager.default.contentsOfDirectory(at:URL(fileURLWithPath:directory),includingPropertiesForKeys:nil).sorted(by:{$0.lastPathComponent<$1.lastPathComponent}) where ["gif","png"].contains(url.pathExtension){
 guard let s=CGImageSourceCreateWithURL(url as CFURL,nil),let img=CGImageSourceCreateImageAtIndex(s,0,nil) else{fatalError("Unreadable image")}
 let count=CGImageSourceGetCount(s)
 if url.pathExtension=="gif"{precondition(count==65,"Animation frame count changed")}
 precondition(img.width==1100 && img.height==720,"Unexpected image size")
 rows.append(["file":url.lastPathComponent,"frames":count,"width":img.width,"height":img.height])
}
let json=try JSONSerialization.data(withJSONObject:rows,options:[.prettyPrinted,.sortedKeys]);print(String(data:json,encoding:.utf8)!)
