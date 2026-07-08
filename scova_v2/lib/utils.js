import { clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import React from 'react'

export function cn(...inputs) {
  return twMerge(clsx(inputs))
}

/**
 * Splits text into highlighted spans and plain text.
 * @param {string} text - The original essay text.
 * @param {Array} highlights - Array of {start, end, category, reason}
 * @returns {Array} - Array of React elements or strings.
 */
export function renderHighlightedEssay(text, highlights) {
  if (!text) return "";
  if (!highlights || highlights.length === 0) return text;

  // Sort highlights by start position
  const sortedHighlights = [...highlights].sort((a, b) => a.start - b.start);

  const result = [];
  let lastIndex = 0;

  sortedHighlights.forEach((h, index) => {
    // Add text before highlight
    if (h.start > lastIndex) {
      result.push(text.substring(lastIndex, h.start));
    }

    // Add highlighted span
    const highlightText = text.substring(h.start, h.end);
    const className = `hl ${h.category === 'strong' ? 'hl-strong' : 'hl-weak'}`;
    
    result.push(
      <mark 
        key={`hl-${index}`} 
        className={className} 
        data-tooltip={h.reason}
      >
        {highlightText}
      </mark>
    );

    lastIndex = h.end;
  });

  // Add remaining text
  if (lastIndex < text.length) {
    result.push(text.substring(lastIndex));
  }

  return result;
}
