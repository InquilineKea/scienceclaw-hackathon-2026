// Original bounded Ritz-eigensolver regression; standard library only.
#include <vector>
#include <utility>
#include <cmath>
#include <limits>
#include <algorithm>
#include <iostream>
using V=std::vector<double>;
std::pair<double,double>eig(std::vector<V>A){int n=A.size();for(int it=0;it<20000;it++){int p=0,q=1;double best=0;for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(std::abs(A[i][j])>best){best=std::abs(A[i][j]);p=i;q=j;}if(best<1e-11)break;double phi=.5*std::atan2(2*A[p][q],A[q][q]-A[p][p]),c=std::cos(phi),s=std::sin(phi),a=A[p][p],b=A[q][q],d=A[p][q];for(int k=0;k<n;k++)if(k!=p&&k!=q){double x=A[k][p],y=A[k][q];A[k][p]=A[p][k]=c*x-s*y;A[k][q]=A[q][k]=s*x+c*y;}A[p][p]=c*c*a-2*s*c*d+s*s*b;A[q][q]=s*s*a+2*s*c*d+c*c*b;A[p][q]=A[q][p]=0;}double lo=INFINITY,hi=-INFINITY;for(int i=0;i<n;i++){lo=std::min(lo,A[i][i]);hi=std::max(hi,A[i][i]);}return{lo,hi};}
int main(){
 std::vector<std::vector<V>> cases={{{2,0},{0,-3}},{{2,1},{1,2}},{{0,2},{2,0}},{{1}}};
 double lo[]={-3,1,-2,1},hi[]={2,3,2,1};
 for(int i=0;i<4;i++){auto q=eig(cases[i]);if(std::abs(q.first-lo[i])>1e-12||std::abs(q.second-hi[i])>1e-12)return 2;}
 // Orthogonal similarity of a diagonal matrix with a single resolved negative mode.
 int n=32;std::vector<V>A(n,V(n,0));for(int i=0;i<n;i++)A[i][i]=i?i+1:-.125;
 for(int t=0;t<50;t++){int p=t%n,q=(t*7+3)%n;if(p==q)continue;double c=std::cos(.37),s=std::sin(.37);for(int k=0;k<n;k++){double x=A[k][p],y=A[k][q];A[k][p]=c*x-s*y;A[k][q]=s*x+c*y;}for(int k=0;k<n;k++){double x=A[p][k],y=A[q][k];A[p][k]=c*x-s*y;A[q][k]=s*x+c*y;}}
 auto q=eig(A);if(std::abs(q.first+.125)>1e-9||std::abs(q.second-32)>1e-9)return 3;
 std::cout<<"5 exact-spectrum Ritz matrix checks passed; min="<<q.first<<" max="<<q.second<<"\n";
}
