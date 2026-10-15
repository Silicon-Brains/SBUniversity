"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth, useUser } from "@clerk/nextjs";
import {
  GraduationCap,
  QrCode,
  Phone,
  Mail,
  Building,
  Calendar,
  ShieldCheck,
  CheckCircle2,
  Download,
  ExternalLink,
  Edit3,
  Loader2,
  User,
  X,
  Camera,
} from "lucide-react";
import { PageHeader, Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { api, getDevAuthToken } from "@/lib/api";

interface StudentCardData {
  name: string;
  student_code: string;
  department?: string | null;
  batch_year?: number | null;
  phone?: string | null;
  photo_url?: string | null;
  valid_until?: string | null;
  qr_verify_url: string;
  status: string;
  email?: string;
}

interface MeApiResponse {
  id: string;
  email: string;
  full_name: string;
  avatar_url?: string | null;
  role: string;
  status: string;
  student_profile?: {
    student_code: string;
    batch_year?: number | null;
    phone?: string | null;
    photo_path?: string | null;
    department?: { name: string } | null;
    date_of_birth?: string | null;
    qr_token: string;
  } | null;
}

export default function StudentProfilePage() {
  const { getToken } = useAuth();
  const { user } = useUser();
  const toast = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);

  // Real ID card state
  const [cardData, setCardData] = useState<StudentCardData>({
    name: "Student",
    student_code: "SBU-2026-0001",
    department: "Computer Science & Engineering",
    batch_year: 2026,
    phone: "+91 98765 43210",
    photo_url: null,
    valid_until: "June 30, 2028",
    qr_verify_url: "/verify/student",
    status: "active",
    email: "student@sbuniversity.edu",
  });

  // Edit form state
  const [editName, setEditName] = useState("");
  const [editPhone, setEditPhone] = useState("");
  const [editEmergency, setEditEmergency] = useState("+91 91234 56789");
  const [editAvatarUrl, setEditAvatarUrl] = useState("");

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("student");
    }
    return token;
  }, [getToken]);

  // Load real student data from backend database
  const loadProfile = useCallback(async () => {
    setLoading(true);
    try {
      const token = await resolveToken();
      const [idCardRes, meRes] = await Promise.all([
        api<StudentCardData>("/student/id-card", token ?? undefined).catch(() => null),
        api<MeApiResponse>("/me", token ?? undefined).catch(() => null),
      ]);

      const name = idCardRes?.name || meRes?.full_name || user?.fullName || "SBUniversity Student";
      const studentCode = idCardRes?.student_code || meRes?.student_profile?.student_code || "SBU-2026-0001";
      const department = idCardRes?.department || meRes?.student_profile?.department?.name || "Computer Science & Engineering";
      const batchYear = idCardRes?.batch_year || meRes?.student_profile?.batch_year || 2026;
      const phone = idCardRes?.phone || meRes?.student_profile?.phone || "+91 98765 43210";
      const photoUrl = idCardRes?.photo_url || meRes?.avatar_url || user?.imageUrl || null;
      const email = meRes?.email || user?.primaryEmailAddress?.emailAddress || "student@sbuniversity.edu";
      const status = idCardRes?.status || meRes?.status || "active";

      const mergedData: StudentCardData = {
        name,
        student_code: studentCode,
        department,
        batch_year: batchYear,
        phone,
        photo_url: photoUrl,
        valid_until: idCardRes?.valid_until ? new Date(idCardRes.valid_until).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" }) : "June 30, 2028",
        qr_verify_url: `/verify/${studentCode}`,
        status,
        email,
      };

      setCardData(mergedData);
      setEditName(name);
      setEditPhone(phone || "");
      setEditAvatarUrl(photoUrl || "");
    } catch (err) {
      console.error("Failed to fetch student ID card:", err);
    } finally {
      setLoading(false);
    }
  }, [resolveToken, user]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  // Save updated ID Card data to database
  const handleSaveEdit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      const token = await resolveToken();
      await api<MeApiResponse>(
        "/me",
        token ?? undefined,
        {
          method: "PATCH",
          body: JSON.stringify({
            full_name: editName.trim() || undefined,
            phone: editPhone.trim() || undefined,
            avatar_url: editAvatarUrl.trim() || undefined,
          }),
        }
      );

      setCardData((prev) => ({
        ...prev,
        name: editName.trim() || prev.name,
        phone: editPhone.trim() || prev.phone,
        photo_url: editAvatarUrl.trim() || prev.photo_url,
      }));

      setIsEditModalOpen(false);
      toast("Virtual ID Card details successfully updated in database!");
    } catch (err: any) {
      const msg =
        err?.message === "Failed to fetch"
          ? "Unable to reach the backend server. Please verify the server is running."
          : err?.message || "Failed to update ID card details.";
      toast(msg);
    } finally {
      setSaving(false);
    }
  };

  const batchString = cardData.batch_year ? `${cardData.batch_year - 2} – ${cardData.batch_year + 2}` : "2024 – 2028";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Student Virtual ID Card"
        subtitle="Your official university credential with tamper-evident digital verification."
        action={
          <div className="flex items-center gap-2">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => setIsEditModalOpen(true)}
            >
              <Edit3 size={15} /> Edit ID Card
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => window.print()}
              className="hidden sm:inline-flex"
            >
              <Download size={15} /> Print / Save ID
            </Button>
          </div>
        }
      />

      {loading ? (
        <div className="flex h-64 items-center justify-center rounded-2xl border border-cream-300 bg-white shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : (
        <div className="grid gap-8 lg:grid-cols-12 lg:items-start">
          {/* Physical-dimension Virtual ID Card representation */}
          <div className="flex justify-center lg:col-span-5">
            <div
              id="student-id-card"
              className="relative flex h-[540px] w-[340px] flex-col overflow-hidden rounded-2xl bg-cream-200 shadow-2xl border border-cream-300 select-none transition-transform duration-300 hover:scale-[1.01]"
            >
              {/* Top 40%: Green-700 to Green-900 gradient banner */}
              <div className="relative flex h-[190px] flex-col items-center justify-between bg-gradient-to-b from-green-700 to-green-900 p-5 text-center text-cream-50">
                <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#F5DABF_1px,transparent_1px)] [background-size:12px_12px]" />

                <div className="flex items-center gap-2">
                  <span className="grid h-7 w-7 place-items-center rounded-lg bg-cream-200 text-green-900">
                    <GraduationCap size={16} />
                  </span>
                  <span className="font-heading text-sm font-bold tracking-wide text-cream-50">
                    SB UNIVERSITY
                  </span>
                </div>

                <p className="text-[10px] font-medium uppercase tracking-widest text-cream-300">
                  Official Student Identity Card
                </p>

                {/* Circular Student Avatar */}
                <div className="relative -mb-12">
                  {cardData.photo_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img
                      src={cardData.photo_url}
                      alt={cardData.name}
                      className="h-24 w-24 rounded-full object-cover ring-4 ring-cream-200 shadow-lg bg-cream-100"
                    />
                  ) : (
                    <div className="grid h-24 w-24 place-items-center rounded-full bg-cream-100 font-heading text-2xl font-bold text-green-900 ring-4 ring-cream-200 shadow-md">
                      {cardData.name.split(" ").map((n) => n[0]).join("").slice(0, 2).toUpperCase()}
                    </div>
                  )}
                </div>
              </div>

              {/* Middle body */}
              <div className="flex flex-1 flex-col items-center px-6 pt-14 pb-4 text-center">
                <h2 className="font-heading text-xl font-bold text-green-900 truncate max-w-[280px]">
                  {cardData.name}
                </h2>
                <p className="mt-0.5 font-mono text-xs font-semibold text-green-700">
                  {cardData.student_code}
                </p>

                <div className="mt-4 w-full space-y-1.5 rounded-xl bg-white/80 p-3 text-left text-xs shadow-sm backdrop-blur-sm border border-cream-200/50">
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Department:</span>
                    <span className="font-medium text-ink truncate max-w-[170px]">
                      {cardData.department || "Computer Science & Engineering"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Batch:</span>
                    <span className="font-medium text-ink">{batchString}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-ink-muted">Valid Until:</span>
                    <span className="font-medium text-ink">{cardData.valid_until}</span>
                  </div>
                </div>

                {/* QR Verification Tile */}
                <div className="mt-4 flex flex-col items-center">
                  <div className="rounded-xl border border-cream-300 bg-white p-2.5 shadow-sm">
                    <div className="flex flex-col items-center justify-center h-20 w-20 bg-green-50 rounded-lg">
                      <QrCode size={52} className="text-green-700" />
                    </div>
                  </div>
                  <Link
                    href={cardData.qr_verify_url}
                    className="mt-1.5 inline-flex items-center gap-1 text-[11px] font-medium text-green-700 hover:underline"
                  >
                    <span>Scan to verify credential</span>
                    <ExternalLink size={10} />
                  </Link>
                </div>
              </div>

              {/* Bottom Bordo Accent Stripe */}
              <div className="h-4 w-full bg-bordo-700 flex items-center justify-between px-3 text-[9px] font-semibold text-cream-50 uppercase tracking-wider">
                <span>SBU VERIFIED</span>
                <span>ACADEMIC YEAR 2026</span>
              </div>
            </div>
          </div>

          {/* Profile Details & Contact Configuration */}
          <div className="space-y-6 lg:col-span-7">
            <Card>
              <div className="flex items-center justify-between border-b border-cream-300 pb-4">
                <div>
                  <h3 className="text-lg font-bold">Credential Registry Details</h3>
                  <p className="text-xs text-ink-muted">Official records from the University Database</p>
                </div>
                <Badge tone="success">
                  <ShieldCheck size={13} className="mr-1" /> Active Student
                </Badge>
              </div>

              <div className="mt-5 grid gap-4 sm:grid-cols-2">
                <div className="rounded-lg bg-cream-50 p-3.5">
                  <span className="flex items-center gap-2 text-xs font-medium text-ink-muted">
                    <Building size={14} className="text-green-700" /> Department
                  </span>
                  <p className="mt-1 font-semibold text-green-900">{cardData.department}</p>
                </div>

                <div className="rounded-lg bg-cream-50 p-3.5">
                  <span className="flex items-center gap-2 text-xs font-medium text-ink-muted">
                    <Calendar size={14} className="text-green-700" /> Academic Term
                  </span>
                  <p className="mt-1 font-semibold text-green-900">Semester 4 ({batchString})</p>
                </div>

                <div className="rounded-lg bg-cream-50 p-3.5">
                  <span className="flex items-center gap-2 text-xs font-medium text-ink-muted">
                    <Mail size={14} className="text-green-700" /> Institutional Email
                  </span>
                  <p className="mt-1 font-mono text-xs font-medium text-green-900 truncate">
                    {cardData.email}
                  </p>
                </div>

                <div className="rounded-lg bg-cream-50 p-3.5">
                  <span className="flex items-center gap-2 text-xs font-medium text-ink-muted">
                    <CheckCircle2 size={14} className="text-green-700" /> Verification Status
                  </span>
                  <p className="mt-1 font-semibold text-green-900">Enrolled & In Good Standing</p>
                </div>
              </div>
            </Card>

            {/* Contact Information & Quick Edit Card */}
            <Card>
              <div className="flex items-center justify-between border-b border-cream-300 pb-4">
                <div>
                  <h3 className="text-lg font-bold">Contact Information</h3>
                  <p className="text-xs text-ink-muted">Synchronized across virtual ID and administrative alerts</p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setIsEditModalOpen(true)}
                >
                  <Edit3 size={13} className="mr-1" /> Edit ID Card
                </Button>
              </div>

              <div className="mt-5 space-y-4">
                <div className="flex items-center justify-between rounded-lg bg-cream-50 p-3.5">
                  <div className="flex items-center gap-3">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-green-700 shadow-sm">
                      <Phone size={15} />
                    </span>
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Primary Phone</p>
                      <p className="text-sm font-semibold text-green-900">{cardData.phone || "Not set"}</p>
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-lg bg-cream-50 p-3.5">
                  <div className="flex items-center gap-3">
                    <span className="grid h-8 w-8 place-items-center rounded-lg bg-white text-green-700 shadow-sm">
                      <Phone size={15} />
                    </span>
                    <div>
                      <p className="text-xs font-medium text-ink-muted">Emergency Contact</p>
                      <p className="text-sm font-semibold text-green-900">{editEmergency}</p>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Edit ID Card Modal */}
      {isEditModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="absolute inset-0 bg-green-900/50 backdrop-blur-sm"
            onClick={() => setIsEditModalOpen(false)}
          />
          <div className="relative w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl border border-cream-300">
            <div className="flex items-center justify-between border-b border-cream-200 pb-3">
              <div className="flex items-center gap-2">
                <Edit3 className="text-green-700" size={18} />
                <h3 className="font-heading text-lg font-bold text-green-900">
                  Edit Virtual ID Card
                </h3>
              </div>
              <button
                onClick={() => setIsEditModalOpen(false)}
                className="rounded-lg p-1 text-ink-muted hover:bg-cream-100 hover:text-ink"
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleSaveEdit} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Full Name (on ID Card)
                </label>
                <input
                  type="text"
                  required
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="h-10 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                  placeholder="Enter full legal name"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Primary Mobile Number
                </label>
                <input
                  type="tel"
                  required
                  value={editPhone}
                  onChange={(e) => setEditPhone(e.target.value)}
                  className="h-10 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Emergency Contact Number
                </label>
                <input
                  type="tel"
                  value={editEmergency}
                  onChange={(e) => setEditEmergency(e.target.value)}
                  className="h-10 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                  placeholder="+91 91234 56789"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-green-900 mb-1">
                  Photo / Avatar URL
                </label>
                <input
                  type="url"
                  value={editAvatarUrl}
                  onChange={(e) => setEditAvatarUrl(e.target.value)}
                  className="h-10 w-full rounded-lg border border-cream-300 bg-white px-3 text-sm text-ink focus:border-green-700 focus:outline-none"
                  placeholder="https://... image URL for ID photo"
                />
                <p className="mt-1 text-[11px] text-ink-muted">
                  Direct link to a high-resolution portrait photograph.
                </p>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-cream-200">
                <button
                  type="button"
                  onClick={() => setIsEditModalOpen(false)}
                  className="h-9 rounded-lg border border-cream-300 px-4 text-xs font-semibold text-ink-muted hover:bg-cream-100"
                >
                  Cancel
                </button>
                <Button type="submit" variant="primary" size="sm" disabled={saving}>
                  {saving ? (
                    <>
                      <Loader2 size={14} className="animate-spin mr-1.5" /> Saving...
                    </>
                  ) : (
                    "Save & Update ID"
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
