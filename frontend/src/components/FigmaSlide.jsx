import React from 'react';

const CubeIcon = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 32 32"
    xmlns="http://www.w3.org/2000/svg"
    className="h-8 w-8 text-white"
  >
    <path
      d="M16 3.5 4.5 9.5v13l11.5 6 11.5-6v-13Z"
      fill="currentColor"
      opacity="0.12"
    />
    <path
      d="M16 3.5 4.5 9.5l11.5 6 11.5-6Z"
      fill="currentColor"
    />
    <path
      d="m16 28.5 11.5-6v-13L16 15.5v13Z"
      fill="currentColor"
      opacity="0.28"
    />
    <path
      d="m16 28.5-11.5-6v-13L16 15.5v13Z"
      fill="currentColor"
      opacity="0.44"
    />
  </svg>
);

const ArrowIcon = () => (
  <svg
    aria-hidden="true"
    viewBox="0 0 24 24"
    xmlns="http://www.w3.org/2000/svg"
    className="h-5 w-5"
  >
    <path
      d="m6.75 17.25 6.5-6.5-6.5-6.5M10 10.75h7.25"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeWidth="1.75"
    />
  </svg>
);

const FigmaSlide = () => {
  return (
    <section className="relative flex min-h-screen w-full items-center justify-center overflow-hidden bg-gradient-to-b from-[#17140f] via-[#231a23] to-[#362932] px-6 py-16 text-white">
      <div
        aria-hidden="true"
        className="absolute inset-0 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.08),_transparent_58%)]"
      />
      <div
        aria-hidden="true"
        className="absolute right-[8%] top-[14%] h-16 w-40 rounded-[32px] bg-black/50 backdrop-blur"
      />

      <div className="relative z-10 w-full max-w-3xl space-y-12">
        <div className="flex flex-col gap-6 text-white/90">
          <span className="inline-flex h-12 w-12 items-center justify-center rounded-2xl border border-white/20 bg-white/10 backdrop-blur-md shadow-[0_16px_40px_rgba(0,0,0,0.35)]">
            <CubeIcon />
          </span>

          <div className="space-y-6 text-sm leading-relaxed md:text-base">
            <p>
              Figma is a comprehensive design tool that enables teams to create, share, and test designs for digital
              products and experiences [1]. It empowers designers, product managers, writers, developers, and anyone
              involved in the design process to contribute, give feedback, and make better decisions—faster [1].
            </p>

            <div className="space-y-3">
              <p className="text-base font-semibold text-white md:text-lg">Key Features of Figma</p>
              <p>
                Figma offers a range of capabilities that make it an ideal tool for design and collaboration. Some of the
                standout highlights include:
              </p>
              <ul className="list-disc space-y-2 pl-5 text-white/80">
                <li>Real-time collaboration across every stakeholder</li>
                <li>Reusable component libraries for cohesive design systems</li>
                <li>FigJam whiteboarding for quick exploration and alignment</li>
              </ul>
            </div>
          </div>
        </div>

        <form className="w-full" onSubmit={(event) => event.preventDefault()}>
          <label className="sr-only" htmlFor="figma-slide-input">
            Describe your ideal tool for design and collaboration
          </label>
          <div className="flex items-center rounded-[36px] border border-white/12 bg-white/5 px-8 py-6 shadow-[0_24px_52px_rgba(0,0,0,0.45)] backdrop-blur-md">
            <input
              id="figma-slide-input"
              type="text"
              placeholder="Ideal tool for design and collaboration"
              className="flex-1 bg-transparent text-sm text-white placeholder-white/60 outline-none md:text-base"
            />
            <button
              type="submit"
              className="ml-6 flex h-12 w-12 items-center justify-center rounded-full bg-white text-[#362932] transition hover:bg-[#f4f1ff] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              <span className="sr-only">Submit insight</span>
              <ArrowIcon />
            </button>
          </div>
        </form>
      </div>
    </section>
  );
};

export default FigmaSlide;
