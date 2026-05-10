/** Wenqu API client module for liya-ai.
 *
 * This module is original code, independent of the Open WebUI fork.
 * Provides API calls for the academic interview (问渠) system.
 */

import { WEBUI_API_BASE_URL } from '$lib/constants';

const WENQU_BASE = `${WEBUI_API_BASE_URL}/wenqu`;

async function fetchWithAuth(token: string, url: string, options: RequestInit = {}) {
    const res = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...options.headers,
            authorization: `Bearer ${token}`
        }
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || 'Request failed');
    }
    return res.json();
}

export interface Project {
    title: string;
    description: string;
    tech_stack: string[];
    role: string;
    highlights: string[];
}

export interface ParsedResume {
    projects: Project[];
    publications: any[];
    skills: string[];
    competitions: any[];
}

export interface ScoredProject {
    title: string;
    risk_score: number;
    reason: string;
}

export interface InterviewRound {
    id: string;
    session_id: string;
    round_number: number;
    question: string;
    question_type: string;
    answer: string | null;
    evaluation: string | null;
    depth_score: number | null;
    created_at: number;
    updated_at: number;
}

export interface FeedbackReport {
    id: string;
    session_id: string;
    academic_score: number;
    expression_score: number;
    authenticity_score: number;
    risk_flags: string[];
    improvement_suggestions: string[];
    full_report: string;
    created_at: number;
}

export interface WenquSession {
    id: string;
    user_id: string;
    project_title: string | null;
    project_description: string | null;
    resume_text: string | null;
    status: string;
    created_at: number;
    updated_at: number;
}

/** Parse resume text and extract structured project information. */
export const parseResume = async (token: string, resumeText: string): Promise<ParsedResume> => {
    return fetchWithAuth(token, `${WENQU_BASE}/parse-resume`, {
        method: 'POST',
        body: JSON.stringify({ resume_text: resumeText })
    });
};

/** Select the most vulnerable project for deep questioning. */
export const selectProject = async (
    token: string,
    projects: Project[]
): Promise<{ selected_project: Project; all_scored: ScoredProject[] }> => {
    return fetchWithAuth(token, `${WENQU_BASE}/select-project`, {
        method: 'POST',
        body: JSON.stringify({ projects })
    });
};

/** Create a new interview session. */
export const createSession = async (
    token: string,
    data: { resume_text: string; project_title: string; project_description: string }
): Promise<{ session: WenquSession }> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions`, {
        method: 'POST',
        body: JSON.stringify(data)
    });
};

/** Get all sessions for the current user. */
export const getSessions = async (token: string): Promise<WenquSession[]> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions`);
};

/** Get a specific session by ID. */
export const getSession = async (token: string, sessionId: string): Promise<WenquSession> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions/${sessionId}`);
};

/** Start the interview — generates the first question. */
export const startInterview = async (
    token: string,
    sessionId: string
): Promise<{ round: InterviewRound; round_number: number }> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions/${sessionId}/start`, {
        method: 'POST'
    });
};

/** Submit an answer and get the next question. */
export const submitAnswer = async (
    token: string,
    sessionId: string,
    answer: string
): Promise<{
    round: InterviewRound;
    next_question: string | null;
    interview_complete: boolean;
}> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions/${sessionId}/answer`, {
        method: 'POST',
        body: JSON.stringify({ answer })
    });
};

/** Get all rounds for a session. */
export const getRounds = async (
    token: string,
    sessionId: string
): Promise<InterviewRound[]> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions/${sessionId}/rounds`);
};

/** Generate feedback report for a completed session. */
export const generateFeedback = async (
    token: string,
    sessionId: string
): Promise<{ report: FeedbackReport }> => {
    return fetchWithAuth(token, `${WENQU_BASE}/sessions/${sessionId}/feedback`, {
        method: 'POST'
    });
};
