import Foundation
import AppKit

let root=URL(fileURLWithPath:CommandLine.arguments[1])
func readJSON(_ path:String)->[String:Any] {return try! JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent(path))) as! [String:Any]}
let comparison=readJSON("outputs/mace-mp-followup/comparison.json")
let rows=comparison["rows"] as! [[String:Any]]
let off=readJSON("outputs/evidence/existing_crosslink_params.json")["crosslinks"] as! [String:[String:Any]]
let mp=readJSON("outputs/mace-mp-followup/mace_mp_result.json")["crosslinks"] as! [String:[String:Any]]
let ink=NSColor(calibratedRed:0.08,green:0.15,blue:0.22,alpha:1)
let teal=NSColor(calibratedRed:0.02,green:0.43,blue:0.48,alpha:1)
let orange=NSColor(calibratedRed:0.78,green:0.29,blue:0.08,alpha:1)
let gray=NSColor(calibratedRed:0.42,green:0.47,blue:0.52,alpha:1)
let grid=NSColor(calibratedWhite:0.88,alpha:1)
let light=NSColor(calibratedRed:0.96,green:0.975,blue:0.985,alpha:1)
class Canvas {
 let w:CGFloat;let h:CGFloat;let rep:NSBitmapImageRep
 init(_ width:Int,_ height:Int){w=CGFloat(width);h=CGFloat(height);rep=NSBitmapImageRep(bitmapDataPlanes:nil,pixelsWide:width,pixelsHigh:height,bitsPerSample:8,samplesPerPixel:4,hasAlpha:true,isPlanar:false,colorSpaceName:.deviceRGB,bytesPerRow:0,bitsPerPixel:0)!;let ctx=NSGraphicsContext(bitmapImageRep:rep)!.cgContext;ctx.translateBy(x:0,y:h);ctx.scaleBy(x:1,y:-1);NSGraphicsContext.current=NSGraphicsContext(cgContext:ctx,flipped:true);NSColor.white.setFill();NSBezierPath(rect:NSRect(x:0,y:0,width:w,height:h)).fill()}
 func text(_ s:String,_ x:CGFloat,_ y:CGFloat,_ width:CGFloat,_ size:CGFloat=22,_ color:NSColor=ink,_ bold:Bool=false,_ height:CGFloat=100){let style=NSMutableParagraphStyle();style.lineBreakMode = .byWordWrapping;let font=NSFont.systemFont(ofSize:size,weight:bold ? .semibold:.regular);(s as NSString).draw(in:NSRect(x:x,y:y,width:width,height:height),withAttributes:[.font:font,.foregroundColor:color,.paragraphStyle:style])}
 func line(_ x1:CGFloat,_ y1:CGFloat,_ x2:CGFloat,_ y2:CGFloat,_ color:NSColor=grid,_ width:CGFloat=1){color.setStroke();let p=NSBezierPath();p.move(to:NSPoint(x:x1,y:y1));p.line(to:NSPoint(x:x2,y:y2));p.lineWidth=width;p.stroke()}
 func box(_ x:CGFloat,_ y:CGFloat,_ w:CGFloat,_ h:CGFloat,_ color:NSColor=light){color.setFill();NSBezierPath(roundedRect:NSRect(x:x,y:y,width:w,height:h),xRadius:14,yRadius:14).fill()}
 func dot(_ x:CGFloat,_ y:CGFloat,_ r:CGFloat,_ color:NSColor){color.setFill();NSBezierPath(ovalIn:NSRect(x:x-r,y:y-r,width:r*2,height:r*2)).fill()}
 func arrow(_ x1:CGFloat,_ y1:CGFloat,_ x2:CGFloat,_ y2:CGFloat,_ color:NSColor=gray){line(x1,y1,x2,y2,color,3);let a=atan2(y2-y1,x2-x1);line(x2,y2,x2-14*cos(a-0.45),y2-14*sin(a-0.45),color,3);line(x2,y2,x2-14*cos(a+0.45),y2-14*sin(a+0.45),color,3)}
 func save(_ name:String){let d=rep.representation(using:.png,properties:[:])!;try! d.write(to:root.appendingPathComponent("outputs/figures/"+name));print(name,d.count)}
}
func name(_ s:String)->String {return s=="isopeptide_TG2" ? "Isopeptide / TG2 proxy" : s=="pyridinoline" ? "Pyridinoline proxy" : s=="glucosepane" ? "Glucosepane proxy" : s.prefix(1).uppercased()+s.dropFirst()}
do {
 let c=Canvas(1600,1060)
 c.text("Model choice changes proxy-fragment curvature",65,40,1470,40,ink,true)
 c.text("Eight source fragments • same anchor-distance grids • five-point local quadratic fits",65,101,1470,23,gray)
 c.dot(91,166,8,teal);c.text("MACE-OFF23 medium",111,148,400,23,teal,true)
 c.dot(575,166,8,orange);c.text("MACE-MP-0b2 medium",595,148,470,23,orange,true)
 let x0:CGFloat=405,x1:CGFloat=1175,y0:CGFloat=245,dy:CGFloat=76
 let lo=log10(0.03),hi=log10(2.0)
 func sx(_ v:Double)->CGFloat{return x0+CGFloat((log10(v)-lo)/(hi-lo))*(x1-x0)}
 for v in [0.03,0.05,0.1,0.2,0.5,1.0,2.0]{let x=sx(v);c.line(x,y0-20,x,y0+dy*7+24);c.text(String(format:"%.2g",v),x-25,y0+dy*7+40,80,20,gray)}
 c.text("OFF",1252,196,100,20,teal,true);c.text("MP",1400,196,100,20,orange,true)
 for (i,r) in rows.enumerated(){let y=y0+CGFloat(i)*dy;let a=r["k_OFF_eV_A2"] as! Double,b=r["k_MP_eV_A2"] as! Double;let label=name(r["source_proxy_label"] as! String)
 c.text(label,65,y-17,320,24,ink,true);c.line(sx(a),y,sx(b),y,NSColor(calibratedWhite:0.68,alpha:1),4);c.dot(sx(a),y,10,teal);c.dot(sx(b),y,10,orange);c.text(String(format:"%.4f",a),1243,y-17,130,23,teal);c.text(String(format:"%.4f",b),1388,y-17,140,23,orange)}
 c.text("Fitted curvature k (eV/Å²) — logarithmic horizontal axis",405,865,950,23,ink,true)
 c.box(60,920,1480,105);c.text("These are simplified proxy structures, not validated native crosslinks or collagen stiffness.",83,936,1430,22,ink,true);c.text("Boundary minima: sulfilimine (OFF), pyridinoline proxy (MP). Local fits do not establish equilibrium stiffness.",83,974,1430,21,gray)
 c.save("mace-off-vs-mp-curvature.png")
}
do {
 let c=Canvas(1800,1280)
 c.text("All eight constrained energy curves",55,35,1690,42,ink,true)
 c.text("Each model's curve is separately zeroed at its own sampled minimum. Vertical scales differ between panels.",55,100,1690,24,gray)
 c.line(65,164,115,164,teal,4);c.text("MACE-OFF23 medium",130,147,420,24,teal,true);c.line(660,164,710,164,orange,4);c.text("MACE-MP-0b2 medium",725,147,600,24,orange,true)
 for (i,r) in rows.enumerated(){let n=r["source_proxy_label"] as! String;let col=i%4,row=i/4;let left=CGFloat(55+col*440),top=CGFloat(220+row*460);c.box(left,top,410,425)
 c.text(name(n),left+18,top+18,380,24,ink,true)
 let a=off[n]!,b=mp[n]!;let L=a["L_A"] as! [Double],l0=a["L0_A"] as! Double;let e0=a["E_eV"] as! [Double],e1=b["E_eV"] as! [Double];let ymax=ceil(max(e0.max()!,e1.max()!)*10)/10
 let px=left+62,py=top+90,pw:CGFloat=322,ph:CGFloat=250
 func sx(_ v:Double)->CGFloat{return px+CGFloat((v+0.06)/0.31)*pw};func sy(_ v:Double)->CGFloat{return py+ph-CGFloat(v/ymax)*ph}
 for f in [0.0,0.5,1.0]{let y=sy(ymax*f);c.line(px,y,px+pw,y,grid,1);c.text(String(format:"%.2f",ymax*f),left+8,y-12,52,16,gray)}
 for strain in [-0.06,0.0,0.1,0.2,0.25]{let x=sx(strain);c.line(x,py,x,py+ph,grid,1);c.text(String(format:"%.0f",strain*100),x-15,py+ph+10,50,16,gray)}
 c.text("ΔE (eV)",left+18,top+57,180,18,gray);c.text("Imposed anchor strain (%)",px-9,top+385,340,19,gray)
 for (es,color) in [(e0,teal),(e1,orange)]{for j in 1..<L.count{c.line(sx(L[j-1]/l0-1),sy(es[j-1]),sx(L[j]/l0-1),sy(es[j]),color,3)};for j in 0..<L.count{c.dot(sx(L[j]/l0-1),sy(es[j]),2.8,color)}}
 }
 c.text("21 points per fragment and model. Different relaxed structures may contribute to differences; this is not a same-geometry benchmark.",55,1160,1690,22,ink,true)
 c.text("Source labels include a neutral pyridinoline proxy and an approximate glucosepane core. Curves do not establish rupture or reaction behavior.",55,1210,1690,21,gray)
 c.save("mace-off-vs-mp-energy-curves.png")
}
do {
 let c=Canvas(1600,1030)
 c.text("What this collagen pipeline actually establishes",65,40,1470,40,ink,true)
 c.text("Completed calculations, separate evidence streams, and the limit on biological interpretation",65,104,1470,23,gray)
 c.box(65,190,455,270);c.text("NEW H100 PILOT",90,212,400,21,teal,true);c.text("4 neutral molecules\n2 seeds each",90,254,395,30,ink,true,100);c.text("RDKit / MMFF input checks\nALCHEMI FIRE2 + MACE-OFF23\n8/8 numerical checks passed",90,355,395,23,ink,false,100)
 c.box(65,510,455,290);c.text("RECOVERED L4 SCANS",90,532,400,21,orange,true);c.text("8 simplified proxy fragments\n21 anchor distances each",90,574,395,29,ink,true,100);c.text("MACE-OFF + MACE-MP completed\n12 earlier fragment–GAG scans\nProxy chemistry remains unvalidated",90,678,395,22,ink,false,100)
 c.box(650,285,385,355);c.text("CHECK & COMPARE",675,310,330,22,ink,true);c.text("Finite data and matched grids\nIndependent fit arithmetic\nCurves and model sensitivity\nHashes, job logs and costs",675,367,330,24,ink,false,210)
 c.arrow(520,325,650,390,teal);c.arrow(520,650,650,530,orange)
 c.box(1160,285,375,355);c.text("PUBLISH & DISPLAY",1185,310,325,22,ink,true);c.text("WordPress report + raw data\nRead-only explorer evidence\nNo tissue-parameter updates",1185,367,320,24,ink,false,210);c.arrow(1035,460,1160,460)
 c.box(65,860,1470,120,NSColor(calibratedRed:1,green:0.95,blue:0.91,alpha:1));c.text("Not established: native crosslink rupture, glucosepane/PYD/4-HNE reactions, or collagen/tissue stiffness.",90,882,1420,25,ink,true,80);c.text("Numerical completion and two-model agreement do not provide experimental validation.",90,940,1410,22,gray)
 c.save("collagen-pipeline-evidence-diagram.png")
}
