// Original dependency-free sensitivity solver; no imported simulation code.
#include <algorithm>
#include <array>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <numeric>
#include <map>
#include <tuple>
#include <random>
#include <stdexcept>
#include <string>
#include <vector>
using V=std::vector<double>;
struct P{double x,y;};
struct E{int i,j;double x,y;};
struct B{int i,j,k;double x,y;};
struct Mesh{std::vector<P> p;std::vector<E> e;std::vector<B>b;std::vector<int>outer,adh;};
double norm(const V&v){double s=0;for(double x:v)s+=x*x;return std::sqrt(s);}
V cholsolve(V a,V rhs,int n){
 for(int i=0;i<n;i++)for(int j=0;j<=i;j++){double s=a[i*n+j];for(int k=0;k<j;k++)s-=a[i*n+k]*a[j*n+k];if(i==j){if(!(s>1e-14))throw std::runtime_error("nonpositive constrained Hessian");a[i*n+j]=std::sqrt(s);}else a[i*n+j]=s/a[j*n+j];}
 for(int i=0;i<n;i++){for(int k=0;k<i;k++)rhs[i]-=a[i*n+k]*rhs[k];rhs[i]/=a[i*n+i];}
 for(int i=n-1;i>=0;i--){for(int k=i+1;k<n;k++)rhs[i]-=a[k*n+i]*rhs[k];rhs[i]/=a[i*n+i];}return rhs;
}
Mesh mesh(int side,int seed,double density){
 Mesh m;std::mt19937 gen(seed);std::uniform_real_distribution<double>rand(0,1);
 for(int j=0;j<side;j++)for(int i=0;i<side;i++){
 P p{double(i)+.5*(j%2)-(side-1)*.5,double(j)*std::sqrt(3)/2-(side-1)*std::sqrt(3)/4};double r=std::hypot(p.x,p.y);if(r<.99)continue;int n=m.p.size();m.p.push_back(p);
 if(i==0||j==0||i==side-1||j==side-1)m.outer.push_back(n);else if(r<1.8)m.adh.push_back(n);
 }
 for(int i=0;i<(int)m.p.size();i++)for(int j=i+1;j<(int)m.p.size();j++){double x=m.p[j].x-m.p[i].x,y=m.p[j].y-m.p[i].y;if(std::abs(std::hypot(x,y)-1)<1e-7&&rand(gen)<density)m.e.push_back({i,j,x,y});}
 for(int j=0;j<(int)m.p.size();j++){std::vector<int> ns;for(auto e:m.e){if(e.i==j)ns.push_back(e.j);if(e.j==j)ns.push_back(e.i);}for(int a=0;a<(int)ns.size();a++)for(int c=a+1;c<(int)ns.size();c++){int i=ns[a],k=ns[c];if(std::hypot(m.p[i].x+m.p[k].x-2*m.p[j].x,m.p[i].y+m.p[k].y-2*m.p[j].y)<1e-7)m.b.push_back({i,j,k,-(m.p[i].y-m.p[j].y),m.p[i].x-m.p[j].x});}}
 if(m.adh.size()<4)throw std::runtime_error("too few adhesions");return m;
}
std::vector<int> selection(const Mesh&m,int seed,bool cluster){std::vector<int> ids(m.e.size());std::iota(ids.begin(),ids.end(),0);int count=std::lround(.35*ids.size());if(cluster){double ang=(seed-4700)%8*std::acos(-1)/4;P c{1.6*std::cos(ang),1.6*std::sin(ang)};std::sort(ids.begin(),ids.end(),[&](int a,int b){auto dist=[&](int q){auto e=m.e[q];return std::hypot((m.p[e.i].x+m.p[e.j].x)/2-c.x,(m.p[e.i].y+m.p[e.j].y)/2-c.y);};return dist(a)<dist(b);});}else{std::mt19937 gen(seed+5100);std::shuffle(ids.begin(),ids.end(),gen);}std::vector<int> mask(ids.size(),0);for(int q=0;q<count;q++)mask[ids[q]]=1;return mask;}
using Key=std::pair<int,int>;
Key pointkey(P p){return {int(std::lround(p.x*2)),int(std::lround(p.y*2/std::sqrt(3)))};}
Mesh embedded(int seed,double density){
 Mesh core=mesh(7,seed,density),m;std::map<Key,int> old;for(int i=0;i<(int)core.p.size();i++)old[pointkey(core.p[i])]=i;
 for(int j=-4;j<=4;j++)for(int i=-4;i<=4;i++){int parity=((j+1)%2+2)%2;P p{double(i)+.5*parity,j*std::sqrt(3)/2};double r=std::hypot(p.x,p.y);if(r<.99)continue;int n=m.p.size();m.p.push_back(p);if(i==-4||i==4||j==-4||j==4)m.outer.push_back(n);else if(r<1.8)m.adh.push_back(n);}
 std::mt19937 gen(seed+20000);std::uniform_real_distribution<double>rand(0,1);
 for(int i=0;i<(int)m.p.size();i++)for(int j=i+1;j<(int)m.p.size();j++){double x=m.p[j].x-m.p[i].x,y=m.p[j].y-m.p[i].y;if(std::abs(std::hypot(x,y)-1)>1e-7)continue;auto ai=old.find(pointkey(m.p[i])),aj=old.find(pointkey(m.p[j]));bool retain=false;if(ai!=old.end()&&aj!=old.end()){for(auto e:core.e)if((e.i==ai->second&&e.j==aj->second)||(e.i==aj->second&&e.j==ai->second)){retain=true;break;}}else retain=rand(gen)<density;if(retain)m.e.push_back({i,j,x,y});}
 for(int j=0;j<(int)m.p.size();j++){std::vector<int>ns;for(auto e:m.e){if(e.i==j)ns.push_back(e.j);if(e.j==j)ns.push_back(e.i);}for(int a=0;a<(int)ns.size();a++)for(int c=a+1;c<(int)ns.size();c++){int i=ns[a],k=ns[c];if(std::hypot(m.p[i].x+m.p[k].x-2*m.p[j].x,m.p[i].y+m.p[k].y-2*m.p[j].y)<1e-7)m.b.push_back({i,j,k,-(m.p[i].y-m.p[j].y),m.p[i].x-m.p[j].x});}}
 return m;
}
std::vector<int> embedded_selection(const Mesh&m,int seed,bool cluster,double density){auto core=mesh(7,seed,density);auto mask=selection(core,seed,cluster);std::vector<int> out(m.e.size());int found=0;for(int q=0;q<(int)core.e.size();q++)if(mask[q]){auto a=pointkey(core.p[core.e[q].i]),b=pointkey(core.p[core.e[q].j]);for(int k=0;k<(int)m.e.size();k++){auto x=pointkey(m.p[m.e[k].i]),y=pointkey(m.p[m.e[k].j]);if((x==a&&y==b)||(x==b&&y==a)){out[k]=1;found++;break;}}}if(found!=std::accumulate(mask.begin(),mask.end(),0))throw std::runtime_error("core selected edge lost");return out;}
struct R{double r,tangent;};
R response(double z,double a,int law){
 if(law==0)return{z,1};
 if(law==1)return{z/(1+a),1/(1+a)};
 if(law==2){double y=.01;if(std::abs(z)<=y)return{z,1};return{(z+std::copysign(a*y,z))/(1+a),1/(1+a)};}
 // Implicit Eyring rate strengthening: r+a*e0*sinh(r/e0)=z.
 double e0=.01,lo=0,hi=std::abs(z),r=hi/(1+a);
 for(int it=0;it<35;it++){double s=r+a*e0*std::sinh(r/e0)-std::abs(z);if(std::abs(s)<1e-13)break;if(s>0)hi=r;else lo=r;double q=r-s/(1+a*std::cosh(r/e0));r=(q>lo&&q<hi)?q:(lo+hi)/2;}
 return{std::copysign(r,z),1/(1+a*std::cosh(r/e0))};
}
struct Eval{V g,h;double energy=0;};
Eval eval(const Mesh&m,const std::vector<int>&mask,double contrast,double scale,double bend,int law,double ratio,double dt,const V&slip,const V&u,const std::vector<int>&map,int nf,double kc,const V&target,bool matrix){
 Eval v;v.g.assign(u.size(),0);if(matrix)v.h.assign(nf*nf,0);
 auto add=[&](const std::vector<int>&ids,const V&coef,double force,double tangent){for(int a=0;a<(int)ids.size();a++){v.g[ids[a]]+=coef[a]*force;if(matrix&&map[ids[a]]>=0)for(int b=0;b<(int)ids.size();b++)if(map[ids[b]]>=0)v.h[map[ids[a]]*nf+map[ids[b]]]+=coef[a]*coef[b]*tangent;}};
 for(int q=0;q<(int)m.e.size();q++){auto e=m.e[q];double ext=e.x*(u[2*e.j]-u[2*e.i])+e.y*(u[2*e.j+1]-u[2*e.i+1]);double k=scale*(mask[q]?contrast:1),tau=mask[q]?ratio:1;R r=response(ext-slip[q],dt/tau,law);double eq=law==0?0:.2,ks=k*(1-eq);double f=k*eq*ext+ks*r.r;add({2*e.i,2*e.i+1,2*e.j,2*e.j+1},{-e.x,-e.y,e.x,e.y},f,k*eq+ks*r.tangent);v.energy+=.5*k*eq*ext*ext+.5*ks*r.r*r.r;}
 for(auto b:m.b){std::vector<int> ids{2*b.i,2*b.i+1,2*b.j,2*b.j+1,2*b.k,2*b.k+1};V c{b.x,b.y,-2*b.x,-2*b.y,b.x,b.y};double z=0;for(int a=0;a<6;a++)z+=c[a]*u[ids[a]];add(ids,c,scale*bend*z,scale*bend);v.energy+=.5*scale*bend*z*z;}
 if(kc>0)for(int n:m.adh)for(int d=0;d<2;d++){int i=2*n+d;double z=u[i]-target[i];v.g[i]+=kc*z;if(matrix&&map[i]>=0)v.h[map[i]*nf+map[i]]+=kc;v.energy+=.5*kc*z*z;}
 return v;
}
struct Sol{V u;double residual=0;int iter=0;};
Sol equilibrium(const Mesh&m,const std::vector<int>&mask,double contrast,double scale,double bend,int law,double ratio,double dt,const V&slip,V u,const std::vector<int>&fixed,const V&target,double kc){
 std::vector<int> map(u.size(),-1),free;std::vector<int> pin(u.size(),0);for(int i:fixed){pin[2*i]=pin[2*i+1]=1;u[2*i]=target[2*i];u[2*i+1]=target[2*i+1];}for(int i=0;i<(int)u.size();i++)if(!pin[i]){map[i]=free.size();free.push_back(i);}int nf=free.size();double residual=0;
 for(int it=0;it<40;it++){
  auto v=eval(m,mask,contrast,scale,bend,law,ratio,dt,slip,u,map,nf,kc,target,true);V rhs(nf);for(int q=0;q<nf;q++)rhs[q]=-v.g[free[q]];residual=norm(rhs);if(residual<1e-10)return{u,residual,it};V step=cholsolve(v.h,rhs,nf);double t=1;V trial=u;
  bool accepted=false;for(int ls=0;ls<25;ls++){trial=u;for(int q=0;q<nf;q++)trial[free[q]]+=t*step[q];auto w=eval(m,mask,contrast,scale,bend,law,ratio,dt,slip,trial,map,nf,kc,target,false);V g;for(int i:free)g.push_back(w.g[i]);if(norm(g)<residual*(1-1e-4*t)||norm(g)<1e-10){accepted=true;break;}t*=.5;}if(!accepted)throw std::runtime_error("Newton line search failed");u=trial;
 }
 throw std::runtime_error("equilibrium failed");
}
double shear(const Mesh&m,const std::vector<int>&mask,double contrast,double bend){V u(2*m.p.size(),0),slip(m.e.size(),0),target=u;for(int n:m.outer)target[2*n]=.01*m.p[n].y;auto s=equilibrium(m,mask,contrast,1,bend,0,1,.05,slip,u,m.outer,target,0);std::vector<int>dummy(u.size(),-1);return eval(m,mask,contrast,1,bend,0,1,.05,slip,s.u,dummy,0,0,target,false).energy;}
struct Metrics{double ramp=0,end=0,auc=0,peak=0,cv=0,retention=0,diss=0,residualforce=0,residual=0,forcebalance=0;int maxiter=0;};
Metrics simulate(const Mesh&m,const std::vector<int>&mask,double contrast,double scale,double bend,int law,double ratio,double dt,int cell,std::ofstream*trace,int seed,int side,double density){
 V u(2*m.p.size(),0),slip(m.e.size(),0),target=u;auto fixed=m.outer;if(!cell)fixed.insert(fixed.end(),m.adh.begin(),m.adh.end());double kc=cell?.2:0;Metrics stats;double previous=0;
 int steps=std::lround(10/dt);
 for(int step=1;step<=steps;step++){
  double t=step*dt,amp=.04*(t<=1?t:t<=5?1:t<=6?6-t:0);std::fill(target.begin(),target.end(),0);for(int n:m.adh){double r=std::hypot(m.p[n].x,m.p[n].y);target[2*n]=-amp*m.p[n].x/r;target[2*n+1]=-amp*m.p[n].y/r;}
  auto s=equilibrium(m,mask,contrast,scale,bend,law,ratio,dt,slip,u,fixed,target,kc);u=s.u;stats.residual=std::max(stats.residual,s.residual);stats.maxiter=std::max(stats.maxiter,s.iter);
  std::vector<int>dummy(u.size(),-1);auto v=eval(m,mask,contrast,scale,bend,law,ratio,dt,slip,u,dummy,0,0,target,false);
  V mags;double fx=0,fy=0;for(int n:m.outer){fx+=v.g[2*n];fy+=v.g[2*n+1];}for(int n:m.adh){double x=cell?kc*(target[2*n]-u[2*n]):v.g[2*n],y=cell?kc*(target[2*n+1]-u[2*n+1]):v.g[2*n+1];fx+=x;fy+=y;mags.push_back(std::hypot(x,y));}stats.forcebalance=std::max(stats.forcebalance,std::hypot(fx,fy));double mean=std::accumulate(mags.begin(),mags.end(),0.)/mags.size(),sd=0;for(double f:mags)sd+=(f-mean)*(f-mean);sd=std::sqrt(sd/mags.size());
  if(std::abs(t-1)<dt/10){stats.ramp=mean;stats.peak=*std::max_element(mags.begin(),mags.end());stats.cv=sd/std::max(mean,1e-20);}if(t>1+dt/10&&t<=5+dt/10)stats.auc+=(previous+mean)*dt/2;if(std::abs(t-5)<dt/10)stats.end=mean;if(step==steps)stats.residualforce=mean;previous=mean;
  if(law)for(int q=0;q<(int)m.e.size();q++){auto e=m.e[q];double ext=e.x*(u[2*e.j]-u[2*e.i])+e.y*(u[2*e.j+1]-u[2*e.i+1]);auto r=response(ext-slip[q],dt/(mask[q]?ratio:1),law);double sn=ext-r.r;double diss=.8*scale*(mask[q]?contrast:1)*r.r*(sn-slip[q]);if(diss<-1e-12)throw std::runtime_error("negative sliding dissipation");stats.diss+=std::max(0.,diss);slip[q]=sn;}
  if(trace)*trace<<side<<','<<seed<<','<<density<<','<<bend<<','<<contrast<<','<<law<<','<<ratio<<','<<cell<<','<<scale<<','<<t<<','<<mean<<','<<*std::max_element(mags.begin(),mags.end())<<','<<stats.diss<<'\n';
 }
 stats.retention=stats.end/std::max(stats.ramp,1e-20);if(stats.forcebalance>1e-7)throw std::runtime_error("force balance failed");return stats;
}
void mechanics_checks(std::string root){
 auto m=mesh(7,4700,.95);auto mask=selection(m,4700,false);V u(2*m.p.size()),s(m.e.size(),0),target=u;for(int i=0;i<(int)u.size();i++)u[i]=.002*std::sin(i*.7);std::vector<int>dummy(u.size(),-1);auto v=eval(m,mask,4,1,.03,0,1,.05,s,u,dummy,0,0,target,false);double fdmax=0;for(int i=0;i<(int)u.size();i++){auto a=u,b=u;a[i]+=1e-6;b[i]-=1e-6;double fd=(eval(m,mask,4,1,.03,0,1,.05,s,a,dummy,0,0,target,false).energy-eval(m,mask,4,1,.03,0,1,.05,s,b,dummy,0,0,target,false).energy)/2e-6;fdmax=std::max(fdmax,std::abs(fd-v.g[i]));}for(int i=0;i<(int)u.size();i++)u[i]=i%2?-.7:1;v=eval(m,mask,4,1,.03,0,1,.05,s,u,dummy,0,0,target,false);double tr=norm(v.g);if(fdmax>1e-9||tr>1e-10)throw std::runtime_error("mechanics check failed");
 double r=0;int n=100;for(int i=0;i<n;i++)r=response((i==0?1:r),.05,1).r;double err=std::abs(r-std::pow(1.05,-n));if(err>1e-12)throw std::runtime_error("relaxation analytic check failed");std::ofstream f(root+"/mechanics-checks.json");f<<std::setprecision(17)<<"{\"force_energy_derivative_max_error\":"<<fdmax<<",\"rigid_translation_force_norm\":"<<tr<<",\"single_element_backward_euler_analytic_error\":"<<err<<"}\n";
}
int main(int argc,char**argv){if(argc<2)return 2;std::string root=argv[1],mode=argc>2?argv[2]:"main";try{mechanics_checks(root);}catch(std::exception&e){std::cerr<<e.what();return 1;}std::ofstream out(root+"/"+mode+"-results.csv"),fails(root+"/"+mode+"-failures.csv"),trace(root+"/"+mode+"-traces.csv");out<<std::setprecision(15);trace<<std::setprecision(12);
 out<<"side,seed,density,bending,contrast,law,tau_ratio,cell,architecture,dt,scale,shear_reference,shear_matched,ramp_force,hold_end_force,hold_auc,max_ramp_force,ramp_CV,retention,dissipation,residual_force,equilibrium_residual,force_balance,max_Newton_iterations\n";fails<<"side,seed,density,bending,contrast,law,tau_ratio,cell,architecture,error\n";trace<<"side,seed,density,bending,contrast,law,tau_ratio,cell,scale,time,mean_force,max_force,cumulative_dissipation\n";
 int count=0,failed=0;std::vector<int>sides=(mode=="domain"||mode=="embedded")?std::vector<int>{9}:std::vector<int>{7};double dt=mode=="timestep"?.025:.05;
 for(int side:sides)for(int seed=4700;seed<4712;seed++)for(double density:std::vector<double>{.8,.95})for(double bend:std::vector<double>{.003,.03}){
  if(mode!="main"&&(bend!=.03||density!=.8))continue;
  Mesh m;double ref;try{m=mode=="embedded"?embedded(seed,density):mesh(side,seed,density);ref=shear(m,std::vector<int>(m.e.size(),0),1,bend);}catch(std::exception&e){fails<<side<<','<<seed<<','<<density<<','<<bend<<",0,0,0,0,0,"<<e.what()<<'\n';failed++;continue;}
  for(double contrast:std::vector<double>{.25,1,4})for(int law=0;law<4;law++)for(double ratio:std::vector<double>{.1,1,10}){
   if(law==0&&ratio!=1)continue;if(mode!="main"&&(contrast!=4||ratio==.1))continue;
   for(int cell=0;cell<2;cell++)for(int arch=0;arch<2;arch++)try{
    auto mask=mode=="embedded"?embedded_selection(m,seed,arch,density):selection(m,seed,arch);double initial=shear(m,mask,contrast,bend);double scale=ref/initial;bool tracing=(seed==4700&&density==.8&&bend==.03&&contrast==4&&cell==0);if(tracing)trace<<"# architecture="<<arch<<'\n';auto v=simulate(m,mask,contrast,scale,bend,law,ratio,dt,cell,tracing?&trace:nullptr,seed,side,density);
    out<<side<<','<<seed<<','<<density<<','<<bend<<','<<contrast<<','<<law<<','<<ratio<<','<<cell<<','<<arch<<','<<dt<<','<<scale<<','<<ref<<','<<initial*scale<<','<<v.ramp<<','<<v.end<<','<<v.auc<<','<<v.peak<<','<<v.cv<<','<<v.retention<<','<<v.diss<<','<<v.residualforce<<','<<v.residual<<','<<v.forcebalance<<','<<v.maxiter<<'\n';count++;
   }catch(std::exception&e){fails<<side<<','<<seed<<','<<density<<','<<bend<<','<<contrast<<','<<law<<','<<ratio<<','<<cell<<','<<arch<<','<<e.what()<<'\n';failed++;}
  }
  out.flush();fails.flush();std::cerr<<mode<<" seed "<<seed<<" density "<<density<<" bend "<<bend<<" completed="<<count<<" failed="<<failed<<'\n';
 }
 std::cout<<"completed="<<count<<" failed="<<failed<<'\n';return 0;
}
