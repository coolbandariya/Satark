"""SATARK Radar background.

A Streamlit-friendly adaptation of the React Bits Radar effect. SATARK is a
Streamlit application rather than a React app, so the WebGL component is
mounted through a Streamlit HTML component while keeping the same OGL shader
behavior and public props.

The OGL runtime is loaded from esm.sh in the browser; it is intentionally not
added to Python requirements because it is a browser-side JavaScript
dependency.
"""

from __future__ import annotations
import streamlit.components.v1 as components

_RADAR_HTML = r"""
<!doctype html>
<html><head><meta charset="utf-8"><style>
html,body{margin:0;width:100%;height:100%;overflow:hidden;background:transparent}
canvas{display:block;width:100%;height:100%;opacity:.42}
</style></head><body>
<script type="module">
import { Renderer, Program, Mesh, Triangle } from "https://esm.sh/ogl@1.0.11";
const frame=window.frameElement;
if(frame){frame.style.position="fixed";frame.style.inset="0";frame.style.width="100vw";frame.style.height="100vh";frame.style.zIndex="0";frame.style.border="0";frame.style.pointerEvents="none";frame.setAttribute("aria-hidden","true");}
const root=document.body;
const reduced=matchMedia("(prefers-reduced-motion: reduce)").matches;\nconst settings={speed:reduced?0:.7,scale:.5,ringCount:10,spokeCount:10,ringThickness:.05,spokeThickness:.01,sweepSpeed:reduced?0:.8,sweepWidth:2,sweepLobes:1,color:"#a99cff",backgroundColor:"#050505",falloff:2,brightness:.72,enableMouseInteraction:!reduced,mouseInfluence:.055,lightMode:false};
const hex=h=>{h=h.replace("#","");return[parseInt(h.slice(0,2),16)/255,parseInt(h.slice(2,4),16)/255,parseInt(h.slice(4,6),16)/255]};
const vs="attribute vec2 uv; attribute vec2 position; varying vec2 vUv; void main(){vUv=uv;gl_Position=vec4(position,0,1);}";
const fs="precision highp float; uniform float uTime; uniform vec3 uResolution; uniform float uSpeed,uScale,uRingCount,uSpokeCount,uRingThickness,uSpokeThickness,uSweepSpeed,uSweepWidth,uSweepLobes; uniform vec3 uColor,uBgColor; uniform bool uLightMode; uniform float uFalloff,uBrightness; uniform vec2 uMouse; uniform float uMouseInfluence; uniform bool uEnableMouse; #define TAU 6.28318530718 void main(){vec2 st=gl_FragCoord.xy/uResolution.xy;st=st*2.0-1.0;st.x*=uResolution.x/uResolution.y;if(uEnableMouse){vec2 m=(uMouse*2.0-1.0);m.x*=uResolution.x/uResolution.y;st-=m*uMouseInfluence;}st*=uScale;float d=length(st),a=atan(st.y,st.x),t=uTime*uSpeed;float rp=d*uRingCount-t;float rg=1.0-smoothstep(0.0,uRingThickness,abs(fract(rp)-0.5));float sa=abs(fract(a*uSpokeCount/TAU+0.5)-0.5)*TAU/uSpokeCount;float sg=(1.0-smoothstep(0.0,uSpokeThickness,sa*d))*smoothstep(0.0,0.1,d);float sw=pow(max(0.5*sin(uSweepLobes*a+t*uSweepSpeed)+0.5,0.0),uSweepWidth);float fade=smoothstep(1.05,0.85,d)*pow(max(1.0-d,0.0),uFalloff);vec3 signal=uColor*max((rg+sg+sw)*fade*uBrightness,0.0);vec3 col;if(uLightMode){vec3 mapped=vec3(1.0)-exp(-max(signal,vec3(0.0))*1.45);float e=clamp(max(mapped.r,max(mapped.g,mapped.b)),0.0,1.0);vec3 hue=pow(clamp(mapped/max(e,0.0001),0.0,1.0),vec3(1.2));col=mix(uBgColor,hue,smoothstep(0.015,0.8,e)*.96);gl_FragColor=vec4(col,1.0);}else{col=signal+uBgColor;gl_FragColor=vec4(col,clamp(length(col),0.0,1.0));}}";
const renderer=new Renderer({alpha:true,premultipliedAlpha:false,dpr:Math.min(devicePixelRatio||1,2)}),gl=renderer.gl;
gl.clearColor(0,0,0,0);root.appendChild(gl.canvas);
const program=new Program(gl,{vertex:vs,fragment:fs,uniforms:{
uTime:{value:0},uResolution:{value:[1,1,1]},uSpeed:{value:settings.speed},uScale:{value:settings.scale},uRingCount:{value:settings.ringCount},uSpokeCount:{value:settings.spokeCount},uRingThickness:{value:settings.ringThickness},uSpokeThickness:{value:settings.spokeThickness},uSweepSpeed:{value:settings.sweepSpeed},uSweepWidth:{value:settings.sweepWidth},uSweepLobes:{value:settings.sweepLobes},uColor:{value:hex(settings.color)},uBgColor:{value:hex(settings.backgroundColor)},uLightMode:{value:settings.lightMode},uFalloff:{value:settings.falloff},uBrightness:{value:settings.brightness},uMouse:{value:new Float32Array([.5,.5])},uMouseInfluence:{value:settings.mouseInfluence},uEnableMouse:{value:settings.enableMouseInteraction}}});
const mesh=new Mesh(gl,{geometry:new Triangle(gl),program});let cur=[.5,.5],target=[.5,.5],raf=0;
function resize(){const w=Math.max(1,root.clientWidth),h=Math.max(1,root.clientHeight);renderer.setSize(w,h);program.uniforms.uResolution.value=[gl.canvas.width,gl.canvas.height,gl.canvas.width/gl.canvas.height]}
function move(e){target=[e.clientX/innerWidth,1-e.clientY/innerHeight]} function leave(){target=[.5,.5]}
addEventListener("resize",resize,{passive:true});if(settings.enableMouseInteraction){addEventListener("mousemove",move,{passive:true});addEventListener("mouseleave",leave,{passive:true})}resize();
function tick(time){raf=requestAnimationFrame(tick);program.uniforms.uTime.value=time*.001;cur[0]+=.05*(target[0]-cur[0]);cur[1]+=.05*(target[1]-cur[1]);program.uniforms.uMouse.value[0]=cur[0];program.uniforms.uMouse.value[1]=cur[1];renderer.render({scene:mesh})}raf=requestAnimationFrame(tick);
addEventListener("beforeunload",()=>{cancelAnimationFrame(raf);gl.getExtension("WEBGL_lose_context")?.loseContext()});
</script></body></html>
"""

def render_radar_background() -> None:
    """Mount the full-screen, non-interactive radar background."""
    components.html(_RADAR_HTML, height=1, scrolling=False)
