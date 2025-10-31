export type AttendanceStatus = 'Present' | 'Absent' | 'Late' | string;

export interface AttendanceItem {
  date: string | null;
  status: AttendanceStatus;
  subject: string | null;
  instructor: string | null;
}

export interface AttendanceSummary {
  success: boolean;
  studentId: number;
  today: AttendanceItem[];
  totals: Record<string, number>;
}

export interface AttendanceHistoryResult {
  success: boolean;
  items: AttendanceItem[];
}
