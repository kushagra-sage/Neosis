"use client";
import { create } from "zustand";
import type { CriticScores, DossierItem } from "@/types/api";

export interface StageEvent {
  stage: string;
  at: number;
}

interface InquiryStreamState {
  question: string;
  answer: string;
  stages: StageEvent[];
  currentStage: string | null;
  dossier: DossierItem[];
  critic: Partial<CriticScores> | null;
  followUps: string[];
  inquiryId: string | null;
  isStreaming: boolean;
  error: string | null;

  begin: (question: string) => void;
  pushStage: (stage: string) => void;
  pushToken: (token: string) => void;
  setDossier: (items: DossierItem[]) => void;
  setCritic: (scores: Partial<CriticScores>) => void;
  finish: (inquiryId: string) => void;
  fail: (message: string) => void;
  stop: () => void;
  reset: () => void;
}

/** Extract "Further Research Directions" follow-ups out of the answer text. */
function parseFollowUps(answer: string): string[] {
  const marker = "Further Research Directions:";
  const idx = answer.indexOf(marker);
  if (idx === -1) return [];
  return answer
    .slice(idx + marker.length)
    .split("\n")
    .map((l) => l.replace(/^[\s\d.*-]+/, "").trim())
    .filter((l) => l.includes("?"))
    .slice(0, 3);
}

export const useInquiryStream = create<InquiryStreamState>((set, get) => ({
  question: "",
  answer: "",
  stages: [],
  currentStage: null,
  dossier: [],
  critic: null,
  followUps: [],
  inquiryId: null,
  isStreaming: false,
  error: null,

  begin: (question) =>
    set({
      question,
      answer: "",
      stages: [],
      currentStage: null,
      dossier: [],
      critic: null,
      followUps: [],
      inquiryId: null,
      isStreaming: true,
      error: null,
    }),

  pushStage: (stage) =>
    set((s) => ({
      stages: [...s.stages, { stage, at: Date.now() }],
      currentStage: stage,
    })),

  pushToken: (token) => set((s) => ({ answer: s.answer + token })),

  setDossier: (items) => set({ dossier: items }),
  setCritic: (scores) => set({ critic: scores }),

  finish: (inquiryId) =>
    set({
      inquiryId,
      isStreaming: false,
      currentStage: "done",
      followUps: parseFollowUps(get().answer),
    }),

  fail: (message) =>
    set({ error: message, isStreaming: false, currentStage: "error" }),

  stop: () => set({ isStreaming: false }),

  reset: () =>
    set({
      question: "",
      answer: "",
      stages: [],
      currentStage: null,
      dossier: [],
      critic: null,
      followUps: [],
      inquiryId: null,
      isStreaming: false,
      error: null,
    }),
}));
