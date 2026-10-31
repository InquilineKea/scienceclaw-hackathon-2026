import Foundation
import AppKit
import ImageIO
let W=1200,H=1040
func num(_ x:Any?) -> Double {(x as? NSNumber)?.doubleValue ?? 0}
func color(_ r:Double,_ g:Double,_ b:Double,_ a:Double=1)->NSColor{NSColor(calibratedRed:r,green:g,blue:b,alpha:a)}
let ink=color(0.13,0.23,0.20),paper=color(0.96,0.95,0.92),muted=color(0.40,0.48,0.43)
func box(_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ col:NSColor){col.setFill();NSBezierPath(rect:NSRect(x:x,y:Double(H)-y-h,width:w,height:h)).fill()}
func text(_ s:String,_ x:Double,_ y:Double,_ size:Double=16,_ col:NSColor=ink,_ bold:Bool=false){let f=bold ? NSFont.boldSystemFont(ofSize:size):NSFont.systemFont(ofSize:size);(s as NSString).draw(at:NSPoint(x:x,y:Double(H)-y-size*1.25),withAttributes:[.font:f,.foregroundColor:col])}
func line(_ x:Double,_ y:Double,_ X:Double,_ Y:Double,_ col:NSColor,_ width:Double=1,_ dashed:Bool=false){let p=NSBezierPath();p.move(to:NSPoint(x:x,y:Double(H)-y));p.line(to:NSPoint(x:X,y:Double(H)-Y));p.lineWidth=width;if dashed{p.setLineDash([4,4],count:2,phase:0)};col.setStroke();p.stroke()}
func circle(_ x:Double,_ y:Double,_ radius:Double,_ col:NSColor){col.setFill();NSBezierPath(ovalIn:NSRect(x:x-radius,y:Double(H)-y-radius,width:2*radius,height:2*radius)).fill()}
func image(_ draw:()->Void)->CGImage{let ctx=CGContext(data:nil,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!;NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:false);box(0,0,Double(W),Double(H),paper);draw();NSGraphicsContext.restoreGraphicsState();return ctx.makeImage()!}
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let summaries=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("summary.json"))) as! [[String:Any]]
let cases=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("animation.json"))) as! [[String:Any]]
func png(_ img:CGImage,_ name:String){let p=CGImageDestinationCreateWithURL(root.appendingPathComponent(name+".png") as CFURL,"public.png" as CFString,1,nil)!;CGImageDestinationAddImage(p,img,nil);precondition(CGImageDestinationFinalize(p))}
let green=color(0.17,0.45,0.32),purple=color(0.49,0.29,0.61),red=color(0.8,0.14,0.18)
for key in ["selfAmplitude","farRms"] {
 let img=image {
 text(key=="selfAmplitude" ? "Local oscillatory compliance before and after damage":"Remote response before and after local damage",25,20,30,ink,true)
 text("Mean of 5 seeds and 2 probe directions · dimensionless frequency · same three-fiber lesion within each pair",25,67,17)
 for panel in 0...3 {let n=panel<2 ? 10:14,family=panel%2==0 ? "isotropic":"modular",ox=75.0+Double(panel%2)*590,oy=135.0+Double(panel/2)*383
 let rr=summaries.filter{($0["n"] as! Int)==n && ($0["family"] as! String)==family && num($0["omega"])>0}
 var ys=[Double]();for r in rr {for state in ["intact","damaged"] {let z=num((r[state] as! [String:Any])[key]);if z>0{ys.append(log10(z))}}}
 let low=ys.min()!-0.1,high=ys.max()!+0.1
 let px:(Double)->Double={w in ox+(log10(w)-log10(0.03))/2*435}
 let py:(Double)->Double={v in oy+285-(log10(v)-low)/(high-low)*260}
 text((family=="isotropic" ? "Disordered":"Modular")+" / \(n*n) nodes",ox,oy-25,22,ink,true)
 for w in [0.03,0.1,0.3,1.0,3.0]{let x=px(w);line(x,oy+285,x,oy+291,muted);text(String(format:"%.2g",w),x-14,oy+298,14)}
 for t in 0...3{let value=pow(10,low+(high-low)*Double(t)/3),y=py(value);line(ox,y,ox+435,y,color(0.85,0.87,0.82));text(String(format:"%.3g",value),ox-65,y-10,13)}
 for pattern in ["distributed","clustered"]{for state in ["intact","damaged"]{let col=pattern=="distributed" ? green:purple,points=rr.filter{($0["pattern"] as! String)==pattern}.sorted{num($0["omega"])<num($1["omega"])};var prev:(Double,Double)?=nil
 for r in points{let value=num((r[state] as! [String:Any])[key]),x=px(num(r["omega"])),y=py(value);if let a=prev{line(a.0,a.1,x,y,col,2.5,state=="damaged")};circle(x,y,3,col);prev=(x,y)}
 }}
 text("Frequency Ω = ωγ/kref",ox+120,oy+330,15)
 }
 text("Green: distributed · purple: clustered · solid: intact · dashed: damaged (curves may overlap)",25,923,18,ink,true)
 text(key=="selfAmplitude" ? "Vertical axis (log): |kref × probe displacement / force|":"Vertical axis (log): RMS remote displacement per normalized force; receivers ≥0.6 from probe",25,958,16)
 text("Uniform drag; no solvent hydrodynamics, prestress or calibrated biological time scale. Seed ranges in data.",25,991,15,muted)
 }
 png(img,key=="selfAmplitude" ? "local-compliance":"remote-response")
}
var globalTotal=0.0,globalDelta=0.0
for c in cases{let f=c["fields"] as! [[String:Any]],a=f.first{!($0["damaged"] as! Bool)}!,b=f.first{$0["damaged"] as! Bool}!,ar=a["real"] as! [Double],ai=a["imag"] as! [Double],br=b["real"] as! [Double],bi=b["imag"] as! [Double]
 for j in stride(from:0,to:ar.count,by:2){globalTotal=max(globalTotal,sqrt(ar[j]*ar[j]+ai[j]*ai[j]+ar[j+1]*ar[j+1]+ai[j+1]*ai[j+1]),sqrt(br[j]*br[j]+bi[j]*bi[j]+br[j+1]*br[j+1]+bi[j+1]*bi[j+1]));globalDelta=max(globalDelta,sqrt(pow(br[j]-ar[j],2)+pow(bi[j]-ai[j],2)+pow(br[j+1]-ar[j+1],2)+pow(bi[j+1]-ai[j+1],2)))}}
for delta in [false,true]{
 let name=delta ? "damage-induced-response":"oscillatory-response",dst=CGImageDestinationCreateWithURL(root.appendingPathComponent(name+".gif") as CFURL,"com.compuserve.gif" as CFString,41,nil)!
 CGImageDestinationSetProperties(dst,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFLoopCount:0]] as CFDictionary)
 for frame in 0...40 {autoreleasepool{
 let phase=Double(frame)*2*Double.pi/40,img=image{
 text(delta ? "How local damage changes the remote oscillatory response":"Intact and damaged networks under the same oscillatory drive",25,18,27,ink,true)
 text("196 nodes · seed 17 · x drive · Ω=0.1 · phase "+String(format:"%.2f",phase)+" radians",25,61,18)
 for (index,c) in cases.enumerated(){let ox=25.0+Double(index%2)*590,oy=107.0+Double(index/2)*390,net=c["net"] as! [String:Any],X=net["X"] as! [Double],size=num(c["size"]),free=c["free"] as! [Int],edges=net["edges"] as! [[String:Any]],links=net["links"] as! [[String:Any]],lesion=Set(c["lesion"] as! [Int]),probe=Set(c["probe"] as! [Int]),fields=c["fields"] as! [[String:Any]],a=fields.first{!($0["damaged"] as! Bool)}!,b=fields.first{$0["damaged"] as! Bool}!
 let ar=a["real"] as! [Double],ai=a["imag"] as! [Double],br=b["real"] as! [Double],bi=b["imag"] as! [Double]
 box(ox,oy,565,370,color(1,1,1));let family=c["family"] as! String,pattern=c["pattern"] as! String;text((family=="isotropic" ? "Disordered":"Modular")+" / "+pattern,ox+15,oy+12,21,ink,true)
 let sc=280.0/size,px:(Double)->Double={v in ox+142+v*sc},py:(Double)->Double={v in oy+330-v*sc}
 for (k,e) in edges.enumerated(){let i=(e["i"] as! Int)*2,j=(e["j"] as! Int)*2;line(px(X[i]),py(X[i+1]),px(X[j]),py(X[j+1]),lesion.contains(k) ? red:color(0.76,0.8,0.75),lesion.contains(k) ? 2:0.7,lesion.contains(k))}
 for e in links{let i=(e["i"] as! Int)*2,j=(e["j"] as! Int)*2;line(px(X[i]),py(X[i+1]),px(X[j]),py(X[j+1]),color(0.81,0.77,0.87),0.6,true)}
 let scale=35.0/(delta ? globalDelta:globalTotal)
 for j in stride(from:0,to:free.count,by:2){let i=free[j],x=px(X[i]),y=py(X[i+1]);let beforeX=ar[j]*cos(phase)-ai[j]*sin(phase),beforeY=ar[j+1]*cos(phase)-ai[j+1]*sin(phase),afterX=br[j]*cos(phase)-bi[j]*sin(phase),afterY=br[j+1]*cos(phase)-bi[j+1]*sin(phase)
 if !delta{line(x,y,x+beforeX*scale,y-beforeY*scale,color(0.65,0.65,0.65),1.8)}
 let dx=(delta ? afterX-beforeX:afterX)*scale,dy=(delta ? afterY-beforeY:afterY)*scale;line(x,y,x+dx,y-dy,green,1.5);circle(x+dx,y-dy,1.5,green)
 if probe.contains(i/2){circle(x,y,3,color(0.92,0.55,0.1))}
 }
 }
 text(delta ? "Green vectors: damaged minus intact displacement. One shared amplification across all four panels.":"Gray vectors: intact; green: damaged. One shared amplification across all four panels.",25,916,17,ink,true)
 text("Red dashed: 3 cut collagen fibers · pale dashed: added connectors · orange nodes: four-node probe",25,950,16)
 text("Small-amplitude harmonic response with uniform drag. Vectors enlarged for visibility; no new rupture during probing.",25,985,15,muted)
 }
 CGImageDestinationAddImage(dst,img,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFDelayTime:0.09]] as CFDictionary)
 if frame==8{png(img,name+"-still")}
 }}
 precondition(CGImageDestinationFinalize(dst));print("Rendered",name)
}
print("Completed plots and two 41-frame animations")
