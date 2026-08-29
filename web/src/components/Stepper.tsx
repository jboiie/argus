import {
  Children,
  Fragment,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
  type SVGProps,
} from "react";
import { AnimatePresence, motion } from "motion/react";

import "./Stepper.css";

/* Ported from React Bits (JS + CSS + motion), retyped and retoned off its
 * stock indigo palette onto Argus's console/brass one. Used for the
 * Overview tab's walkthrough - a demo aid, not data, so the heavier
 * step-to-step motion earns its place here in a way it wouldn't on a
 * table-reading tab. */

interface StepperProps {
  children: ReactNode;
  initialStep?: number;
  onStepChange?: (step: number) => void;
  onFinalStepCompleted?: () => void;
  backButtonText?: string;
  nextButtonText?: string;
  disableStepIndicators?: boolean;
}

export default function Stepper({
  children,
  initialStep = 1,
  onStepChange = () => {},
  onFinalStepCompleted = () => {},
  backButtonText = "Back",
  nextButtonText = "Continue",
  disableStepIndicators = false,
}: StepperProps) {
  const [currentStep, setCurrentStep] = useState(initialStep);
  const [direction, setDirection] = useState(0);
  const stepsArray = Children.toArray(children);
  const totalSteps = stepsArray.length;
  const isCompleted = currentStep > totalSteps;
  const isLastStep = currentStep === totalSteps;

  const updateStep = (newStep: number) => {
    setCurrentStep(newStep);
    if (newStep > totalSteps) onFinalStepCompleted();
    else onStepChange(newStep);
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setDirection(-1);
      updateStep(currentStep - 1);
    }
  };

  const handleNext = () => {
    if (!isLastStep) {
      setDirection(1);
      updateStep(currentStep + 1);
    }
  };

  const handleComplete = () => {
    setDirection(1);
    updateStep(totalSteps + 1);
  };

  return (
    <div className="stepper-outer">
      <div className="stepper-frame glow-card">
        <div className="stepper-indicator-row">
          {stepsArray.map((_, index) => {
            const stepNumber = index + 1;
            const isNotLastStep = index < totalSteps - 1;
            return (
              <Fragment key={stepNumber}>
                <StepIndicator
                  step={stepNumber}
                  disableStepIndicators={disableStepIndicators}
                  currentStep={currentStep}
                  onClickStep={(clicked) => {
                    setDirection(clicked > currentStep ? 1 : -1);
                    updateStep(clicked);
                  }}
                />
                {isNotLastStep && <StepConnector isComplete={currentStep > stepNumber} />}
              </Fragment>
            );
          })}
        </div>

        <StepContentWrapper isCompleted={isCompleted} currentStep={currentStep} direction={direction}>
          {stepsArray[currentStep - 1]}
        </StepContentWrapper>

        {!isCompleted ? (
          <div className="stepper-footer">
            <div className={`stepper-footer-nav ${currentStep !== 1 ? "spread" : "end"}`}>
              {currentStep !== 1 ? (
                <button onClick={handleBack} className="stepper-back-button">
                  {backButtonText}
                </button>
              ) : null}
              <button onClick={isLastStep ? handleComplete : handleNext} className="stepper-next-button">
                {isLastStep ? "Done" : nextButtonText}
              </button>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function StepContentWrapper({
  isCompleted,
  currentStep,
  direction,
  children,
}: {
  isCompleted: boolean;
  currentStep: number;
  direction: number;
  children: ReactNode;
}) {
  const [parentHeight, setParentHeight] = useState(0);

  return (
    <motion.div
      className="stepper-content-default"
      animate={{ height: isCompleted ? 0 : parentHeight }}
      transition={{ type: "spring", duration: 0.4 }}
    >
      <AnimatePresence initial={false} mode="sync" custom={direction}>
        {!isCompleted ? (
          <SlideTransition key={currentStep} direction={direction} onHeightReady={(h) => setParentHeight(h)}>
            {children}
          </SlideTransition>
        ) : null}
      </AnimatePresence>
    </motion.div>
  );
}

function SlideTransition({
  children,
  direction,
  onHeightReady,
}: {
  children: ReactNode;
  direction: number;
  onHeightReady: (h: number) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
    if (containerRef.current) onHeightReady(containerRef.current.offsetHeight);
  }, [children, onHeightReady]);

  return (
    <motion.div
      ref={containerRef}
      custom={direction}
      variants={stepVariants}
      initial="enter"
      animate="center"
      exit="exit"
      transition={{ duration: 0.4 }}
      className="stepper-slide"
    >
      {children}
    </motion.div>
  );
}

const stepVariants = {
  enter: (dir: number) => ({ x: dir >= 0 ? "-100%" : "100%", opacity: 0 }),
  center: { x: "0%", opacity: 1 },
  exit: (dir: number) => ({ x: dir >= 0 ? "50%" : "-50%", opacity: 0 }),
};

export function Step({ children }: { children: ReactNode }) {
  return <div className="stepper-step">{children}</div>;
}

function StepIndicator({
  step,
  currentStep,
  onClickStep,
  disableStepIndicators,
}: {
  step: number;
  currentStep: number;
  onClickStep: (step: number) => void;
  disableStepIndicators: boolean;
}) {
  const status = currentStep === step ? "active" : currentStep < step ? "inactive" : "complete";

  const handleClick = () => {
    if (step !== currentStep && !disableStepIndicators) onClickStep(step);
  };

  return (
    <motion.div
      onClick={handleClick}
      className="stepper-indicator"
      style={disableStepIndicators ? { pointerEvents: "none", opacity: 0.5 } : {}}
      animate={status}
      initial={false}
    >
      <motion.div
        variants={{
          inactive: { backgroundColor: "var(--color-chrome-2)", color: "var(--color-ink-3)" },
          active: { backgroundColor: "var(--color-brass)", color: "var(--color-void)" },
          complete: { backgroundColor: "var(--color-brass-dim)", color: "var(--color-void)" },
        }}
        transition={{ duration: 0.3 }}
        className="stepper-indicator-inner"
      >
        {status === "complete" ? (
          <CheckIcon className="stepper-check-icon" />
        ) : status === "active" ? (
          <div className="stepper-active-dot" />
        ) : (
          <span className="stepper-step-number">{step}</span>
        )}
      </motion.div>
    </motion.div>
  );
}

function StepConnector({ isComplete }: { isComplete: boolean }) {
  const lineVariants = {
    incomplete: { width: "0%", backgroundColor: "transparent" },
    complete: { width: "100%", backgroundColor: "var(--color-brass)" },
  };

  return (
    <div className="stepper-connector">
      <motion.div
        className="stepper-connector-inner"
        variants={lineVariants}
        initial={false}
        animate={isComplete ? "complete" : "incomplete"}
        transition={{ duration: 0.4 }}
      />
    </div>
  );
}

function CheckIcon(props: SVGProps<SVGSVGElement>) {
  return (
    <svg
      className={props.className}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      <motion.path
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ delay: 0.1, type: "tween", ease: "easeOut", duration: 0.3 }}
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 13l4 4L19 7"
      />
    </svg>
  );
}
