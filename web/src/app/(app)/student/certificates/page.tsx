"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@clerk/nextjs";
import {
  Award,
  Download,
  CheckCircle,
  ExternalLink,
  ShieldCheck,
  QrCode,
  Calendar,
  Sparkles,
  Loader2,
} from "lucide-react";
import { PageHeader, Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useToast } from "@/components/ui/Toast";
import { api, downloadAndOpenPdf, getDevAuthToken } from "@/lib/api";

interface ApiCertificate {
  id: string;
  course_id: string;
  student_id: string;
  certificate_code: string;
  final_percentage: number;
  qr_token: string;
  pdf_path?: string | null;
  issued_at: string;
  revoked_at?: string | null;
  revoke_reason?: string | null;
  course_title?: string | null;
  student_name?: string | null;
}

export default function StudentCertificatesPage() {
  const { getToken } = useAuth();
  const toast = useToast();

  const [certificates, setCertificates] = useState<ApiCertificate[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const resolveToken = useCallback(async () => {
    let token = await getToken();
    if (!token && (process.env.NEXT_PUBLIC_DEMO_MODE === "true" || process.env.NODE_ENV === "development")) {
      token = getDevAuthToken("student");
    }
    return token;
  }, [getToken]);

  const loadCertificates = useCallback(async () => {
    setLoading(true);
    try {
      const token = await resolveToken();
      const data = await api<ApiCertificate[]>("/certificates", token ?? undefined).catch(() => []);
      setCertificates(data || []);
    } catch (err) {
      console.error("Failed to load certificates:", err);
    } finally {
      setLoading(false);
    }
  }, [resolveToken]);

  useEffect(() => {
    loadCertificates();
  }, [loadCertificates]);

  const handleDownloadPdf = async (cert: ApiCertificate) => {
    setDownloadingId(cert.id);
    try {
      const token = await resolveToken();
      const filename = `Certificate_${cert.certificate_code}.pdf`;

      await downloadAndOpenPdf(`/certificates/${cert.id}/pdf`, filename, token ?? undefined);
      toast(`Official Certificate opened in new tab and downloaded for ${cert.course_title || "Course"}!`);
    } catch (err: any) {
      toast(err?.message || "Failed to download Certificate PDF.");
    } finally {
      setDownloadingId(null);
    }
  };

  const activeCerts = certificates.filter((c) => !c.revoked_at);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Certificates of Completion"
        subtitle="Official verified credentials issued upon 100% course exam completion."
      />

      {loading ? (
        <div className="flex h-56 items-center justify-center rounded-2xl border border-cream-300 bg-white shadow-sm">
          <Loader2 className="h-8 w-8 animate-spin text-green-700" />
        </div>
      ) : activeCerts.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-cream-300 bg-white p-12 text-center shadow-sm">
          <Award className="mx-auto h-12 w-12 text-cream-400" />
          <h3 className="mt-3 font-heading text-lg font-bold text-green-900">
            No Course Certificates Earned Yet
          </h3>
          <p className="mt-1 text-sm text-ink-muted max-w-md mx-auto">
            Certificates are issued automatically by the examination engine when you pass all published exams for an enrolled course.
          </p>
          <div className="mt-4">
            <Button href="/student/exams" variant="primary" size="sm">
              Take Course Exams
            </Button>
          </div>
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2">
          {activeCerts.map((cert) => {
            const courseTitle = cert.course_title || "Course Completion";
            const issueDateStr = new Date(cert.issued_at).toLocaleDateString("en-US", {
              month: "long",
              day: "numeric",
              year: "numeric",
            });

            return (
              <div
                key={cert.id}
                className="group relative flex flex-col overflow-hidden rounded-2xl border-2 border-green-700/30 bg-white p-6 shadow-md transition-all hover:border-green-700 hover:shadow-xl"
              >
                {/* Top Certificate Header Banner */}
                <div className="flex items-start justify-between border-b border-cream-200 pb-4">
                  <div className="flex items-center gap-3">
                    <div className="grid h-12 w-12 place-items-center rounded-xl bg-cream-200 text-green-900 shadow-sm">
                      <Award size={26} className="text-bordo-700" />
                    </div>
                    <div>
                      <span className="text-[10px] font-bold uppercase tracking-wider text-green-700">
                        SB UNIVERSITY CREDENTIAL
                      </span>
                      <h3 className="font-heading text-lg font-bold text-green-900">
                        {courseTitle}
                      </h3>
                    </div>
                  </div>
                  <Badge tone="success">
                    <CheckCircle size={12} className="mr-1" /> Verified
                  </Badge>
                </div>

                {/* Certificate Details */}
                <div className="my-5 space-y-2 text-xs text-ink-muted">
                  <div className="flex justify-between">
                    <span>Certificate Code:</span>
                    <span className="font-mono font-bold text-green-900">
                      {cert.certificate_code}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Final Academic Score:</span>
                    <span className="font-semibold text-green-700">
                      {cert.final_percentage}% (Passed with Distinction)
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Issued On:</span>
                    <span className="font-medium text-ink">{issueDateStr}</span>
                  </div>
                </div>

                {/* Verification & Action Bar */}
                <div className="mt-auto flex flex-wrap items-center justify-between gap-3 border-t border-cream-200 pt-4">
                  <Link
                    href={`/verify/${cert.certificate_code}`}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-green-700 hover:underline"
                  >
                    <QrCode size={14} />
                    <span>Verify Credential</span>
                    <ExternalLink size={12} />
                  </Link>

                  <Button
                    variant="primary"
                    size="sm"
                    onClick={() => handleDownloadPdf(cert)}
                    disabled={downloadingId === cert.id}
                  >
                    {downloadingId === cert.id ? (
                      <>
                        <Loader2 size={14} className="animate-spin mr-1.5" /> Downloading...
                      </>
                    ) : (
                      <>
                        <Download size={14} /> Download PDF (New Tab)
                      </>
                    )}
                  </Button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
