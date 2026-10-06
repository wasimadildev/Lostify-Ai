import { useRef } from 'react';
import { ImagePlus, X } from 'lucide-react';

export default function Dropzone({ file, preview, onChange }) {
  const inputRef = useRef(null);

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click();
        }}
        className="border-2 border-dashed border-slate-300 rounded-2xl p-6 flex flex-col items-center justify-center gap-2 cursor-pointer hover:border-blue-400 hover:bg-blue-50/50 transition-colors"
      >
        {preview ? (
          <img src={preview} alt="Report preview" className="h-40 w-full object-cover rounded-xl" />
        ) : (
          <>
            <ImagePlus size={28} className="text-slate-400" />
            <p className="text-sm text-slate-600 font-medium">Add a photo of what was lost</p>
            <p className="text-xs text-slate-400">Optional — but it massively boosts the match</p>
          </>
        )}
      </div>

      {file && (
        <div className="mt-2 flex items-center justify-between bg-slate-100 rounded-xl px-3 py-2">
          <span className="text-xs text-slate-600 truncate">{file.name}</span>
          <button
            type="button"
            onClick={() => {
              onChange?.(null);
              if (inputRef.current) inputRef.current.value = '';
            }}
            className="text-slate-400 hover:text-rose-500 transition-colors"
            aria-label="Remove image"
          >
            <X size={16} />
          </button>
        </div>
      )}

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={(e) => {
          const f = e.target.files?.[0] || null;
          onChange?.(f);
        }}
      />
    </div>
  );
}