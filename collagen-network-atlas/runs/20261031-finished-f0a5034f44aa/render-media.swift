// Original renderer using only macOS system frameworks. No package dependencies.
import Foundation
import AppKit
import ImageIO
let root=URL(fileURLWithPath:FileManager.default.currentDirectoryPath)
let input=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("data/media-input.json"))) as! [String:Any]
let replays=input["replays"] as! [String:[String:Any]],results=input["results"] as! [String:Any]
let W=1100,H=720
func num(_ x:Any?) -> Double {(x as? NSNumber)?.doubleValue ?? 0}
func color(_ r:Double,_ g:Double,_ b:Double,_ a:Double=1)->NSColor{NSColor(calibratedRed:r,green:g,blue:b,alpha:a)}
let ink=color(0.13,0.23,0.20),paper=color(0.96,0.95,0.92),muted=color(0.40,0.48,0.43)
func box(_ x:Double,_ y:Double,_ w:Double,_ h:Double,_ col:NSColor){col.setFill();NSBezierPath(rect:NSRect(x:x,y:Double(H)-y-h,width:w,height:h)).fill()}
func text(_ s:String,_ x:Double,_ y:Double,_ size:Double=16,_ col:NSColor=ink,_ bold:Bool=false){let f=bold ? NSFont.boldSystemFont(ofSize:size):NSFont.systemFont(ofSize:size);(s as NSString).draw(at:NSPoint(x:x,y:Double(H)-y-size*1.25),withAttributes:[.font:f,.foregroundColor:col])}
func line(_ x:Double,_ y:Double,_ X:Double,_ Y:Double,_ col:NSColor,_ width:Double=1,_ dashed:Bool=false){let p=NSBezierPath();p.move(to:NSPoint(x:x,y:Double(H)-y));p.line(to:NSPoint(x:X,y:Double(H)-Y));p.lineWidth=width;if dashed{p.setLineDash([4,4],count:2,phase:0)};col.setStroke();p.stroke()}
func circle(_ x:Double,_ y:Double,_ radius:Double,_ col:NSColor){col.setFill();NSBezierPath(ovalIn:NSRect(x:x-radius,y:Double(H)-y-radius,width:2*radius,height:2*radius)).fill()}
func image(_ draw:()->Void)->CGImage{let ctx=CGContext(data:nil,width:W,height:H,bitsPerComponent:8,bytesPerRow:W*4,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue)!;NSGraphicsContext.saveGraphicsState();NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:false);box(0,0,Double(W),Double(H),paper);draw();NSGraphicsContext.restoreGraphicsState();return ctx.makeImage()!}
func png(_ img:CGImage,_ name:String){let url=root.appendingPathComponent("figures/"+name+".png");let dst=CGImageDestinationCreateWithURL(url as CFURL,"public.png" as CFString,1,nil)!;CGImageDestinationAddImage(dst,img,nil);CGImageDestinationFinalize(dst)}
func frame(_ r:[String:Any],_ q:Double)->[String:Any]{let fs=r["frames"] as! [[String:Any]];return fs.last(where:{num($0["q"])<=q+1e-8}) ?? fs[0]}
for scenario in input["scenarios"] as! [[String:Any]]{
 let keys=scenario["keys"] as! [String],labels=scenario["labels"] as! [String],rr=keys.map{replays[$0]!},id=scenario["id"] as! String
 let dynamic=id=="pulse" || id=="free-vs-clamped",qmax=rr.map{num(($0["frames"] as! [[String:Any]]).last!["q"])}.max()!
 var minX=0.0,maxX=1.0,minY=0.0,maxY=1.0,fmax=0.00000001
 for r in rr{for f in r["frames"] as! [[String:Any]]{let x=f["x"] as! [Double];for i in stride(from:0,to:x.count,by:2){minX=min(minX,x[i]);maxX=max(maxX,x[i]);minY=min(minY,x[i+1]);maxY=max(maxY,x[i+1])};for z in f["forces"] as! [Double]{fmax=max(fmax,abs(z))}}}
 let dst=CGImageDestinationCreateWithURL(root.appendingPathComponent("figures/"+id+".gif") as CFURL,"com.compuserve.gif" as CFString,65,nil)!
 CGImageDestinationSetProperties(dst,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFLoopCount:0]] as CFDictionary)
 for step in 0...64{autoreleasepool{
  let q=qmax*Double(step)/64
  let img=image{
   text("FRACTURE ATLAS / SIMULATION REPLAY",28,15,12,muted,true);text(scenario["title"] as! String,28,42,27,ink,true);text(scenario["subtitle"] as! String,28,82,15,muted)
   text((dynamic ? "Time / t₀" : "Applied strain")+String(format:" = %0.3f",q),28,116,18,ink,true)
   for side in 0...1{let r=rr[side],net=r["net"] as! [String:Any],f=frame(r,q),x=f["x"] as! [Double],X=net["X"] as! [Double],edges=net["edges"] as! [[String:Any]],alive=f["alive"] as! [Bool],forces=f["forces"] as! [Double],ox=28.0+Double(side)*548.0
    box(ox,157,520,370,color(0.08,0.17,0.16));text(labels[side],ox+17,171,22,color(0.91,0.94,0.88),true)
    let sc=min(455/(maxX-minX+0.18),260/(maxY-minY+0.18)),px:(Double)->Double={ox+260+($0-(maxX+minX)/2)*sc},py:(Double)->Double={355-($0-(maxY+minY)/2)*sc}
    for e in edges{let i=(e["i"] as! Int)*2,j=(e["j"] as! Int)*2;line(px(X[i]),py(X[i+1]),px(X[j]),py(X[j+1]),color(0.30,0.43,0.38),0.5)}
    for (k,e) in edges.enumerated(){let i=(e["i"] as! Int)*2,j=(e["j"] as! Int)*2,t=min(1,abs(forces[k])/fmax);let col=alive[k] ? (forces[k]<0 ? color(0.40,0.69,0.90,0.40+0.60*sqrt(t)):color(0.94,0.68,0.42,0.40+0.60*sqrt(t))):color(0.93,0.38,0.45,0.8);line(px(x[i]),py(x[i+1]),px(x[j]),py(x[j+1]),col,alive[k] ? 1+3*t:1,!alive[k])}
    for i in stride(from:0,to:x.count,by:2){circle(px(x[i]),py(x[i+1]),2,color(0.75,0.83,0.73))}
    text(String(format:"Damage %0.1f%%   |   grip reach %0.0f%%",num(f["damage"])*100,num(f["retained"])*100),ox+17,491,14,color(0.88,0.92,0.84))
    let met=r["metrics"] as! [String:Any];text(String(format:"Recorded work to criterion/window: %0.4f × 10⁻³ E₀",num(met["work"])*1000),ox,542,14,ink,true)
    text((met["censored"] as! Bool) ? "Criterion not reached in the protocol window" : met["criterion"] as! String,ox,568,13,muted)
    if dynamic{text(String(format:"Current kinetic energy / (E₀V₀): %0.5f",num(f["kinetic"])),ox,591,13,muted)}
   }
   line(29,638,51,638,color(0.85,0.55,0.28),3);text("tension",60,625,14);line(155,638,177,638,color(0.35,0.63,0.86),3);text("compression",186,625,14);line(330,638,352,638,color(0.90,0.35,0.42),2,true);text("ruptured",361,625,14)
   text("Shared geometry & force scales. Unit square × unit thickness. Original dimensionless toy; no tissue calibration.",28,661,14,muted)
   text(dynamic ? "Material work excludes kinetic energy. No fluid, shock wave or molecular rupture calibration." : "Quasistatic failure traces freeze at their stop. Pressure analogy describes the solid skeleton only.",28,686,13,muted)
  }
  CGImageDestinationAddImage(dst,img,[kCGImagePropertyGIFDictionary:[kCGImagePropertyGIFDelayTime:step==64 ? 1.5:0.12]] as CFDictionary)
  if step==48{png(img,id+"-still")}
 }}
 if !CGImageDestinationFinalize(dst){fatalError("GIF export failed")};print("Rendered",id)
}
let names=["aligned":"Aligned","isotropic":"Disordered","hierarchical":"Hierarchical","modular":"Modular","loops":"Diagonal loops","bottleneck":"Bottleneck","heterogeneous":"Heterogeneous"]
let sums=results["summaries"] as! [[String:Any]]
png(image{
 text("FRACTURE ATLAS / 450 ORIGINAL LOCAL COMPUTATIONS",30,20,13,muted,true);text("The best network depends on the loading regime",30,50,31,ink,true);text("Equal collagen volume 0.06 · 36 nodes · 82 edges · five seeds per family",30,97,17,muted)
 for (column,mode) in ["tension","shear","pulse"].enumerated(){let rr=sums.filter{$0["mode"] as! String==mode},mx=rr.map{(num($0["meanWork"])+num($0["sdWork"]))*1000}.max()!,ox=30.0+Double(column)*357
  text(["X tension","Shear","Constrained pulse"][column],ox,146,23,ink,true)
  for (i,r) in rr.enumerated(){let y=193.0+Double(i)*57,capped=num(r["censored"])>0;let label=names[r["family"] as! String]!+(capped ? " *":"");text(label,ox,y,13);let bx=ox+110,by=y+4,len=num(r["meanWork"])*1000/mx*197,lo=max(0,(num(r["meanWork"])-num(r["sdWork"]))*1000/mx*197),hi=(num(r["meanWork"])+num(r["sdWork"]))*1000/mx*197;box(bx,by,len,15,capped ? color(0.65,0.69,0.61):color(0.30,0.49,0.41));line(bx+lo,by+7.5,bx+hi,by+7.5,ink);line(bx+lo,by+3,bx+lo,by+12,ink);line(bx+hi,by+3,bx+hi,by+12,ink);text(String(format:"%0.3f ± %0.3f",num(r["meanWork"])*1000,num(r["sdWork"])*1000),bx,y+24,12,muted)}
 }
 text("Work density × 10⁻³ E₀. Error bars: sample SD (n=5), not a confidence interval.",30,620,16,ink,true)
 text("* Includes capped runs: protocol work is not complete toughness. Pulse work excludes kinetic energy.",30,650,15,muted)
 text("Hypothetical dimensionless 2D model. No tissue calibration, solvent, shock model or crack-area fracture energy.",30,681,14,muted)
},"benchmark")
print("Rendered benchmark figure")
