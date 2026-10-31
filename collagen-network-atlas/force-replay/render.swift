import Foundation
import AppKit
import ImageIO
let W=1200,H=1020
func num(_ x:Any?) -> Double {(x as? NSNumber)?.doubleValue ?? 0}
func color(_ r:Double,_ g:Double,_ b:Double,_ a:Double=1)->NSColor{NSColor(calibratedRed:r,green:g,blue:b,alpha:a)}
let ink=color(0.13,0.23,0.20),paper=color(0.96,0.95,0.92),muted=color(0.40,0.48,0.43)
func box(_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ col:NSColor){col.setFill();NSBezierPath(rect:NSRect(x:x,y:Double(H)-y-h,width:w,height:h)).fill()}
func text(_ s:String,_ x:Double,_ y:Double,_ size:Double=16,_ col:NSColor=ink,_ bold:Bool=false){let f=bold ? NSFont.boldSystemFont(ofSize:size):NSFont.systemFont(ofSize:size);(s as NSString).draw(at:NSPoint(x:x,y:Double(H)-y-size*1.25),withAttributes:[.font:f,.foregroundColor:col])}
func line(_ x:Double,_ y:Double,_ X:Double,_ Y:Double,_ col:NSColor,_ width:Double=1,_ dashed:Bool=false){let p=NSBezierPath();p.move(to:NSPoint(x:x,y:Double(H)-y));p.line(to:NSPoint(x:X,y:Double(H)-Y));p.lineWidth=width;if dashed{p.setLineDash([4,4],count:2,phase:0)};col.setStroke();p.stroke()}
func circle(_ x:Double,_ y:Double,_ radius:Double,_ col:NSColor){col.setFill();NSBezierPath(ovalIn:NSRect(x:x-radius,y:Double(H)-y-radius,width:2*radius,height:2*radius)).fill()}
func image(_ draw:()->Void)->CGImage{let ctx=CGContext(data:nil,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!;NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:false);box(0,0,Double(W),Double(H),paper);draw();NSGraphicsContext.restoreGraphicsState();return ctx.makeImage()!}
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let d=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("replay.json"))) as! [String:Any]
let cases=d["cases"] as! [[String:Any]],fm=num(d["fmax"]),qm=num(d["qmax"]),xmin=num(d["minX"]),xmax=num(d["maxX"]),ymin=num(d["minY"]),ymax=num(d["maxY"])
let dest=CGImageDestinationCreateWithURL(root.appendingPathComponent("force-redistribution.gif") as CFURL,"com.compuserve.gif" as CFString,81,nil)!
CGImageDestinationSetProperties(dest,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFLoopCount:0]] as CFDictionary)
for step in 0...80 { autoreleasepool {
 let q=qm*Double(step)/80
 let img=image {
 text("FORCE REDISTRIBUTION & DAMAGE / SOLVED MODEL REPLAY",25,16,15,muted,true)
 text("Disordered versus modular collagen networks",25,48,30,ink,true)
 text(String(format:"Same applied strain %.3f · 24 added links · seed 17 · horizontal loading",q),25,94,19)
 for (index,c) in cases.enumerated(){
 let ox=25.0+Double(index%2)*590,oy=142.0+Double(index/2)*367
 let net=c["net"] as! [String:Any],frames=c["frames"] as! [[String:Any]],f=frames.last(where:{num($0["q"])<=q+1e-10}) ?? frames[0]
 let x=f["x"] as! [Double],X=net["X"] as! [Double],edges=net["edges"] as! [[String:Any]],links=net["links"] as! [[String:Any]],alive=f["alive"] as! [Bool],la=f["linkAlive"] as! [Bool],forces=f["forces"] as! [Double],lf=f["linkForces"] as! [Double]
 box(ox,oy,565,350,color(1,1,1))
 let family = c["family"] as! String
 let pattern = c["pattern"] as! String
 let label = (family == "isotropic" ? "Disordered" : "Modular") + " / " + pattern
 text(label,ox+15,oy+10,22,ink,true)
 let scale:Double = min(490.0/(xmax-xmin+0.15),235.0/(ymax-ymin+0.15))
 let midX:Double = (xmin+xmax)/2
 let midY:Double = (ymin+ymax)/2
 let px:(Double)->Double = { v in ox+282+(v-midX)*scale }
 let py:(Double)->Double = { v in oy+167-(v-midY)*scale }
 for group in 0...1 {let es=group==0 ? edges:links,aa=group==0 ? alive:la,ff=group==0 ? forces:lf
 for (k,e) in es.enumerated(){let i=(e["i"] as! Int)*2,j=(e["j"] as! Int)*2,t=min(1,abs(ff[k])/fm),col=aa[k] ? (ff[k]<0 ? color(0.15,0.49,0.78,0.3+0.7*sqrt(t)):color(0.88,0.32,0.06,0.3+0.7*sqrt(t))):color(0.75,0.10,0.37)
 line(px(x[i]),py(x[i+1]),px(x[j]),py(x[j+1]),col,aa[k] ? 0.8+5*sqrt(t):1.4,!aa[k] || group==1)
 }}
 for i in stride(from:0,to:x.count,by:2){let b=X[i]==0 || X[i]==1 || X[i+1]==0 || X[i+1]==1;circle(px(x[i]),py(x[i+1]),b ? 3:2,b ? color(0.1,0.5,0.6):muted)}
 text(String(format:"Collagen lost %.1f%% · connectors broken %.1f%%",num(f["damage"])*100,num(f["linkDamage"])*100),ox+15,oy+291,15)
 let frozen=q>num(frames.last!["q"])+1e-9
 text(frozen ? "STOPPED: "+((c["metrics"] as! [String:Any])["criterion"] as! String):String(format:"Solved strain %.3f · reaction %.4g",num(f["q"]),num(f["force"])),ox+15,oy+319,13,muted)
 }
 text("Orange: tension · blue: compression · width/opacity: |force| on one shared global scale",25,891,17,ink,true)
 text("Dashed: added connectors · magenta dashed: broken elements · blue nodes: prescribed boundary",25,922,16)
 text("Quasistatic states: playback is not physical time. Each trace freezes at its failure criterion.",25,953,16)
 text("Actual solved forces; seed 17 only. Dimensionless 2D hypothesis model; no tissue/AGE calibration.",25,982,15,muted)
 }
 CGImageDestinationAddImage(dest,img,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFDelayTime:step==80 ? 2.0:0.16]] as CFDictionary)
 if step==48 {let p=CGImageDestinationCreateWithURL(root.appendingPathComponent("force-redistribution-still.png") as CFURL,"public.png" as CFString,1,nil)!;CGImageDestinationAddImage(p,img,nil);CGImageDestinationFinalize(p)}
}}
precondition(CGImageDestinationFinalize(dest));print("Rendered 81 frames")
