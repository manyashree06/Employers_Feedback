import React from 'react';

/**
 * AuroraBackground
 * Lightweight, dependency‑free animated aurora background.
 * - Uses several blurred radial blobs animated with keyframes
 * - pointer-events: none so it never blocks UI
 * - fixed + full-bleed so it applies to all pages
 */
export default function AuroraBackground() {
    return (
        <div className="aurora" aria-hidden="true">
            <div className="aurora__blob aurora__blob--a" />
            <div className="aurora__blob aurora__blob--b" />
            <div className="aurora__blob aurora__blob--c" />
            <div className="aurora__blob aurora__blob--d" />
        </div>
    );
}
