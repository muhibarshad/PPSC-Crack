/**
 * GSAP Plugin Registration — Import once in your root layout.
 * Ensures ScrollTrigger and TextPlugin are available globally.
 */
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { TextPlugin } from 'gsap/TextPlugin';

gsap.registerPlugin(ScrollTrigger, TextPlugin);

export { gsap, ScrollTrigger, TextPlugin };
