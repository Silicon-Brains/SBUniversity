"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import {
  ArrowLeft,
  Clock3,
  MessageCircle,
  MessagesSquare,
  Search,
  Send,
  ShieldCheck,
  UsersRound,
} from "lucide-react";
import { api, getDevAuthToken } from "@/lib/api";

type ConversationKind =
  | "student_room"
  | "peer_direct"
  | "admin_support"
  | "teacher_support";

interface Conversation {
  id: string;
  kind: ConversationKind;
  title: string;
  other_user_id?: string | null;
  other_user_role?: "student" | "teacher" | "admin" | null;
  last_message?: string | null;
  last_message_at?: string | null;
  expires_at: string;
  is_shared_room: boolean;
}

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: "student" | "teacher" | "admin";
  sender_avatar_url?: string | null;
  is_mine: boolean;
  content: string;
  created_at: string;
}

interface StudentOption {
  id: string;
  full_name: string;
  avatar_url?: string | null;
}

const ROLE_TOKENS = {
  student: "student",
  teacher: "teacher",
  admin: "admin",
} as const;

function displayTime(value?: string | null): string {
  if (!value) return "";
  return new Date(value).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

function avatarInitials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

export function CommunityChat({ role }: { role: "student" | "teacher" | "admin" }) {
  const { getToken } = useAuth();
  const isStudent = role === "student";
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [students, setStudents] = useState<StudentOption[]>([]);
  const [studentSearch, setStudentSearch] = useState("");
  const [messageText, setMessageText] = useState("");
  const [loadingConversations, setLoadingConversations] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [sending, setSending] = useState(false);
  const [startingConversation, setStartingConversation] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messageEndRef = useRef<HTMLDivElement>(null);
  const manuallyDismissedSelectionRef = useRef(false);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (
      !token &&
      (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")
    ) {
      token = getDevAuthToken(ROLE_TOKENS[role]);
    }
    return token;
  }, [getToken, role]);

  const loadConversations = useCallback(async () => {
    try {
      const token = await resolveToken();
      const data = await api<Conversation[]>("/community-chat/conversations", token ?? undefined);
      setConversations(data);
      setSelectedId((current) =>
        current ?? (manuallyDismissedSelectionRef.current ? null : data[0]?.id ?? null),
      );
      setError(null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "Could not load your chats.");
    } finally {
      setLoadingConversations(false);
    }
  }, [resolveToken]);

  const loadMessages = useCallback(
    async (conversationId: string, showSpinner = false) => {
      if (showSpinner) setLoadingMessages(true);
      try {
        const token = await resolveToken();
        const data = await api<Message[]>(
          `/community-chat/conversations/${conversationId}/messages`,
          token ?? undefined,
        );
        setMessages(data);
      } catch (loadError) {
        setError(loadError instanceof Error ? loadError.message : "Could not load messages.");
      } finally {
        if (showSpinner) setLoadingMessages(false);
      }
    },
    [resolveToken],
  );

  useEffect(() => {
    void loadConversations();
    const timer = window.setInterval(() => void loadConversations(), 10000);
    return () => window.clearInterval(timer);
  }, [loadConversations]);

  useEffect(() => {
    if (!selectedId) {
      setMessages([]);
      return;
    }
    void loadMessages(selectedId, true);
    const timer = window.setInterval(() => void loadMessages(selectedId), 3000);
    return () => window.clearInterval(timer);
  }, [loadMessages, selectedId]);

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  useEffect(() => {
    if (!isStudent) return;
    let active = true;
    const loadStudents = async () => {
      try {
        const token = await resolveToken();
        const data = await api<StudentOption[]>(
          `/community-chat/students?search=${encodeURIComponent(studentSearch)}`,
          token ?? undefined,
        );
        if (active) setStudents(data);
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Could not load students.");
        }
      }
    };
    const timer = window.setTimeout(() => void loadStudents(), studentSearch ? 250 : 0);
    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [isStudent, resolveToken, studentSearch]);

  const selectedConversation = useMemo(
    () => conversations.find((conversation) => conversation.id === selectedId) ?? null,
    [conversations, selectedId],
  );

  async function startDirectChat(student: StudentOption) {
    setStartingConversation(true);
    setError(null);
    try {
      const token = await resolveToken();
      const conversation = await api<Conversation>(
        `/community-chat/direct/${student.id}`,
        token ?? undefined,
        { method: "POST" },
      );
      setConversations((current) => [
        conversation,
        ...current.filter((item) => item.id !== conversation.id),
      ]);
      manuallyDismissedSelectionRef.current = false;
      setSelectedId(conversation.id);
      setStudentSearch("");
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Could not start this chat.");
    } finally {
      setStartingConversation(false);
    }
  }

  async function startStaffChat(staffRole: "admin" | "teacher") {
    setStartingConversation(true);
    setError(null);
    try {
      const token = await resolveToken();
      const conversation = await api<Conversation>(
        `/community-chat/staff/${staffRole}`,
        token ?? undefined,
        { method: "POST" },
      );
      setConversations((current) => [
        conversation,
        ...current.filter((item) => item.id !== conversation.id),
      ]);
      manuallyDismissedSelectionRef.current = false;
      setSelectedId(conversation.id);
    } catch (startError) {
      setError(startError instanceof Error ? startError.message : "Could not open staff support.");
    } finally {
      setStartingConversation(false);
    }
  }

  async function sendMessage(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedId || !messageText.trim() || sending) return;
    setSending(true);
    setError(null);
    try {
      const token = await resolveToken();
      await api<Message>(
        `/community-chat/conversations/${selectedId}/messages`,
        token ?? undefined,
        {
          method: "POST",
          body: JSON.stringify({ content: messageText }),
        },
      );
      setMessageText("");
      await Promise.all([loadMessages(selectedId), loadConversations()]);
    } catch (sendError) {
      setError(sendError instanceof Error ? sendError.message : "Could not send your message.");
    } finally {
      setSending(false);
    }
  }

  return (
    <section className="flex h-[calc(100dvh-8.75rem)] min-h-[32rem] min-w-0 flex-col overflow-hidden rounded-2xl border border-cream-300 bg-white shadow-sm lg:h-[calc(100dvh-10rem)]">
      <div className="flex min-h-0 flex-1">
        <aside
          className={`w-full shrink-0 flex-col border-r border-cream-200 lg:flex lg:w-[21rem] ${
            selectedConversation ? "hidden" : "flex"
          }`}
          aria-label="Chat conversations"
        >
          <div className="border-b border-cream-200 px-4 py-4">
            <div className="flex items-center gap-2">
              <span className="grid h-10 w-10 place-items-center rounded-xl bg-green-50 text-green-700">
                <MessagesSquare size={20} />
              </span>
              <div>
                <h1 className="font-heading text-lg font-bold text-green-900">Community Chat</h1>
                <p className="text-xs text-ink-muted">
                  {isStudent ? "Connect with your university" : "Support inbox"}
                </p>
              </div>
            </div>
            {isStudent && (
              <div className="mt-4 grid grid-cols-2 gap-2">
                <button
                  type="button"
                  disabled={startingConversation}
                  onClick={() => void startStaffChat("admin")}
                  className="flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-cream-300 bg-cream-50 px-2 text-xs font-semibold text-green-900 transition hover:bg-cream-100 disabled:opacity-50"
                >
                  <ShieldCheck size={15} /> Admin
                </button>
                <button
                  type="button"
                  disabled={startingConversation}
                  onClick={() => void startStaffChat("teacher")}
                  className="flex min-h-11 items-center justify-center gap-1.5 rounded-xl border border-cream-300 bg-cream-50 px-2 text-xs font-semibold text-green-900 transition hover:bg-cream-100 disabled:opacity-50"
                >
                  <UsersRound size={15} /> Teacher
                </button>
              </div>
            )}
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto">
            <div className="space-y-1 p-2">
              {loadingConversations && (
                <p className="px-3 py-4 text-sm text-ink-muted">Loading conversations…</p>
              )}
              {!loadingConversations && conversations.length === 0 && (
                <p className="px-3 py-4 text-sm text-ink-muted">No conversations yet.</p>
              )}
              {conversations.map((conversation) => (
                <button
                  type="button"
                  key={conversation.id}
                  onClick={() => setSelectedId(conversation.id)}
                  className={`flex min-h-[4.5rem] w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition ${
                    selectedId === conversation.id
                      ? "bg-green-50 ring-1 ring-green-100"
                      : "hover:bg-cream-50"
                  }`}
                >
                  <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-green-100 text-green-800">
                    {conversation.is_shared_room ? (
                      <UsersRound size={18} />
                    ) : conversation.kind === "admin_support" ? (
                      <ShieldCheck size={18} />
                    ) : conversation.kind === "teacher_support" ? (
                      <MessageCircle size={18} />
                    ) : (
                      <span className="text-xs font-bold">{avatarInitials(conversation.title)}</span>
                    )}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center justify-between gap-2">
                      <span className="truncate text-sm font-semibold text-green-900">
                        {conversation.title}
                      </span>
                      <span className="shrink-0 text-[10px] text-ink-muted">
                        {displayTime(conversation.last_message_at)}
                      </span>
                    </span>
                    <span className="mt-1 block truncate text-xs text-ink-muted">
                      {conversation.last_message || "Start the conversation"}
                    </span>
                  </span>
                </button>
              ))}
            </div>

            {isStudent && (
              <div className="border-t border-cream-200 p-3">
                <label className="relative block">
                  <Search
                    size={15}
                    className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted"
                  />
                  <input
                    value={studentSearch}
                    onChange={(event) => setStudentSearch(event.target.value)}
                    placeholder="Find a student"
                    aria-label="Find a student to chat with"
                    className="h-11 w-full rounded-xl border border-cream-300 bg-white pl-9 pr-3 text-sm text-ink"
                  />
                </label>
                {(studentSearch || students.length > 0) && (
                  <div className="mt-2 max-h-[calc(100dvh-18rem)] space-y-1 overflow-y-auto">
                    {students.map((student) => (
                      <button
                        type="button"
                        key={student.id}
                        onClick={() => void startDirectChat(student)}
                        disabled={startingConversation}
                        className="flex min-h-11 w-full items-center gap-2 rounded-lg px-2 text-left text-sm text-green-900 hover:bg-cream-50 disabled:opacity-50"
                      >
                        <span className="grid h-8 w-8 shrink-0 place-items-center overflow-hidden rounded-full bg-cream-200 text-[10px] font-bold">
                          {student.avatar_url ? (
                            // eslint-disable-next-line @next/next/no-img-element
                            <img src={student.avatar_url} alt="" className="h-full w-full object-cover" />
                          ) : (
                            avatarInitials(student.full_name)
                          )}
                        </span>
                        <span className="min-w-0 truncate">{student.full_name}</span>
                        <MessageCircle size={14} className="ml-auto shrink-0 text-ink-muted" />
                      </button>
                    ))}
                    {studentSearch && students.length === 0 && (
                      <p className="px-2 py-3 text-xs text-ink-muted">
                        No students match that search.
                      </p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </aside>

        <div
          className={`min-w-0 flex-1 flex-col ${
            selectedConversation ? "flex" : "hidden lg:flex"
          }`}
        >
          {selectedConversation ? (
            <>
              <header className="flex min-h-[4.25rem] items-center gap-3 border-b border-cream-200 px-3 py-2 sm:px-5">
                <button
                  type="button"
                  onClick={() => {
                    manuallyDismissedSelectionRef.current = true;
                    setSelectedId(null);
                  }}
                  className="grid h-11 w-11 shrink-0 place-items-center rounded-xl text-green-700 hover:bg-green-50 lg:hidden"
                  aria-label="Back to conversations"
                >
                  <ArrowLeft size={19} />
                </button>
                <span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-green-100 text-green-800">
                  {selectedConversation.is_shared_room ? (
                    <UsersRound size={18} />
                  ) : (
                    <span className="text-xs font-bold">
                      {avatarInitials(selectedConversation.title)}
                    </span>
                  )}
                </span>
                <div className="min-w-0 flex-1">
                  <h2 className="truncate font-heading text-sm font-bold text-green-900">
                    {selectedConversation.title}
                  </h2>
                  <p className="text-[11px] text-ink-muted">
                    {selectedConversation.is_shared_room
                      ? "Shared student room"
                      : selectedConversation.kind === "admin_support"
                        ? "Private conversation with the admin team"
                        : selectedConversation.kind === "teacher_support"
                          ? "Private conversation with the teacher team"
                          : "Private student conversation"}
                  </p>
                </div>
                <span className="hidden items-center gap-1 text-[11px] text-ink-muted sm:flex">
                  <Clock3 size={13} /> Clears 10 hours after latest message
                </span>
              </header>

              <div
                className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto bg-cream-50/60 px-3 py-4 sm:px-5"
                aria-live="polite"
                aria-label="Messages"
              >
                {loadingMessages && messages.length === 0 && (
                  <p className="m-auto text-sm text-ink-muted">Loading messages…</p>
                )}
                {!loadingMessages && messages.length === 0 && (
                  <div className="m-auto max-w-xs text-center">
                    <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-white text-green-700 shadow-sm">
                      <MessageCircle size={22} />
                    </span>
                    <p className="mt-3 font-semibold text-green-900">Start the conversation</p>
                    <p className="mt-1 text-xs leading-relaxed text-ink-muted">
                      Send a message. This chat and its messages are automatically cleared after
                      10 hours without new activity.
                    </p>
                  </div>
                )}
                {messages.map((message) => {
                  const ownMessage = message.is_mine;
                  return (
                    <div
                      key={message.id}
                      className={`flex w-full ${ownMessage ? "justify-end" : "justify-start"}`}
                    >
                      <article
                        className={`max-w-[88%] rounded-2xl px-3.5 py-2.5 shadow-sm sm:max-w-[75%] ${
                          ownMessage
                            ? "rounded-br-md bg-green-700 text-white"
                            : "rounded-bl-md border border-cream-200 bg-white text-ink"
                        }`}
                      >
                        {!ownMessage && (
                          <p className="mb-1 text-[10px] font-semibold text-green-700">
                            {message.sender_name}
                            <span className="ml-1 capitalize text-ink-muted">
                              · {message.sender_role}
                            </span>
                          </p>
                        )}
                        <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                          {message.content}
                        </p>
                        <time
                          dateTime={message.created_at}
                          className={`mt-1 block text-right text-[10px] ${
                            ownMessage ? "text-cream-200" : "text-ink-muted"
                          }`}
                        >
                          {displayTime(message.created_at)}
                        </time>
                      </article>
                    </div>
                  );
                })}
                <div ref={messageEndRef} />
              </div>

              <form
                onSubmit={sendMessage}
                className="border-t border-cream-200 bg-white p-3 pb-[calc(env(safe-area-inset-bottom)+0.75rem)] sm:px-5"
              >
                {error && (
                  <p role="alert" className="mb-2 text-xs text-danger">
                    {error}
                  </p>
                )}
                <div className="flex items-end gap-2">
                  <textarea
                    value={messageText}
                    onChange={(event) => setMessageText(event.target.value)}
                    onKeyDown={(event) => {
                      if (event.key === "Enter" && !event.shiftKey) {
                        event.preventDefault();
                        event.currentTarget.form?.requestSubmit();
                      }
                    }}
                    rows={1}
                    maxLength={4000}
                    placeholder="Write a message…"
                    aria-label="Message"
                    className="max-h-32 min-h-11 min-w-0 flex-1 resize-y rounded-xl border border-cream-300 bg-cream-50 px-3.5 py-3 text-sm text-ink"
                  />
                  <button
                    type="submit"
                    disabled={sending || !messageText.trim()}
                    aria-label="Send message"
                    className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-bordo-700 text-white transition hover:bg-bordo-500 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <Send size={17} />
                  </button>
                </div>
                <p className="mt-1.5 flex items-center justify-between gap-2 text-[10px] text-ink-muted">
                  <span>Enter to send · Shift+Enter for a new line</span>
                  <span>{messageText.length}/4000</span>
                </p>
              </form>
            </>
          ) : (
            <div className="m-auto hidden max-w-sm px-6 text-center lg:block">
              <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-green-50 text-green-700">
                <MessagesSquare size={26} />
              </span>
              <h2 className="mt-4 font-heading text-lg font-bold text-green-900">
                Your university conversations
              </h2>
              <p className="mt-1 text-sm leading-relaxed text-ink-muted">
                Select a conversation or start a new chat from the list.
              </p>
            </div>
          )}
        </div>
      </div>
      {error && !selectedConversation && (
        <p role="alert" className="border-t border-danger/20 bg-danger-bg px-4 py-2 text-xs text-danger">
          {error}
        </p>
      )}
    </section>
  );
}
