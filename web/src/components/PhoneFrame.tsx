// PhoneFrame — Nokia-style phone shell for USSD and SMS simulators
import { ReactNode } from "react";

interface PhoneFrameProps {
  children: ReactNode;
  title?: string;
}

export default function PhoneFrame({ children, title }: PhoneFrameProps) {
  return (
    <div className="mx-auto w-[280px]">
      {/* Phone shell */}
      <div className="bg-gray-800 rounded-[2.5rem] px-4 pt-6 pb-8 shadow-2xl flex flex-col h-[520px]">
        {/* Top notch */}
        <div className="flex justify-center items-center h-6 mb-2 gap-2">
          <div className="w-16 h-1.5 bg-black rounded-full" />
          <div className="w-2 h-2 bg-gray-600 rounded-full" />
        </div>

        {/* Screen area */}
        <div className="flex-1 bg-black rounded-2xl overflow-hidden flex flex-col shadow-inner">
          {/* Title bar */}
          {title && (
            <div className="bg-gray-900 text-green-400 font-mono text-xs px-3 py-1 text-center tracking-widest border-b border-green-900">
              {title}
            </div>
          )}
          {/* Content area */}
          <div className="flex-1 overflow-y-auto font-mono text-green-400 text-sm p-3 leading-relaxed">
            {children}
          </div>
        </div>

        {/* Bottom bar with home button */}
        <div className="h-8 flex justify-center items-center mt-2">
          <div className="w-10 h-10 bg-gray-700 rounded-full border-2 border-gray-600" />
        </div>
      </div>
    </div>
  );
}
