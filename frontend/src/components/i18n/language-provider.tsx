"use client";

import { createContext, useContext, useEffect, useMemo, useSyncExternalStore } from "react";

export type Locale = "en" | "vi";

const vi: Record<string, string> = {
  Dashboard: "Tổng quan",
  "Detection Events": "Sự kiện phát hiện",
  Incidents: "Sự cố",
  "SOC Copilot": "Trợ lý SOC",
  "Threat Intelligence": "Tình báo mối đe dọa",
  Analytics: "Phân tích",
  "Model Monitor": "Giám sát mô hình",
  "System Monitoring": "Giám sát hệ thống",
  Reports: "Báo cáo",
  "Users & Roles": "Người dùng & vai trò",
  "Audit Logs": "Nhật ký kiểm toán",
  Settings: "Cài đặt",
  Operations: "Vận hành",
  Administration: "Quản trị",
  "System Operational": "Hệ thống hoạt động",
  "Detection services online": "Dịch vụ phát hiện đang trực tuyến",
  "Search event, IP, CVE, IOC...": "Tìm sự kiện, IP, CVE, IOC...",
  "Search security data": "Tìm kiếm dữ liệu bảo mật",
  Notifications: "Thông báo",
  "No new notifications": "Không có thông báo mới",
  "Your alerts and system updates will appear here.": "Cảnh báo và cập nhật hệ thống sẽ xuất hiện tại đây.",
  Navigation: "Điều hướng",
  "Sign out": "Đăng xuất",
  "Public Portfolio Demo": "Bản demo portfolio công khai",
  "Security Overview": "Tổng quan bảo mật",
  "Live Security Operations": "Trung tâm vận hành bảo mật trực tiếp",
  "Monitor security events, active threats, risk scores and detection activity across CyberSentinel AI.": "Theo dõi sự kiện bảo mật, mối đe dọa, điểm rủi ro và hoạt động phát hiện trên CyberSentinel AI.",
  "Security Events Over Time": "Sự kiện bảo mật theo thời gian",
  "Event volume and severity trend from the live detection API.": "Khối lượng sự kiện và xu hướng mức độ từ API phát hiện trực tiếp.",
  "Top Attack Types": "Loại tấn công hàng đầu",
  "Highest-frequency attack categories.": "Các nhóm tấn công xuất hiện nhiều nhất.",
  "Total Events": "Tổng sự kiện",
  "Active Threats": "Mối đe dọa đang hoạt động",
  "Critical Alerts": "Cảnh báo nghiêm trọng",
  "High Alerts": "Cảnh báo mức cao",
  "Medium + Low": "Trung bình + thấp",
  "Average Risk Score": "Điểm rủi ro trung bình",
  "Stored detection events": "Sự kiện phát hiện đã lưu",
  "Requires analyst review": "Cần chuyên viên xem xét",
  "Critical severity": "Mức nghiêm trọng",
  "High severity": "Mức cao",
  "Lower-priority detections": "Phát hiện ưu tiên thấp hơn",
  "Across stored events": "Trên toàn bộ sự kiện đã lưu",
  "Recent Detection Events": "Sự kiện phát hiện gần đây",
  "Latest events returned by the CyberSentinel detection API.": "Các sự kiện mới nhất từ API phát hiện CyberSentinel.",
  "View all": "Xem tất cả",
  "Severity Distribution": "Phân bố mức độ",
  "Top Threat Sources": "Nguồn đe dọa hàng đầu",
  "Threat Level": "Mức đe dọa",
  "Live Data Source": "Nguồn dữ liệu trực tiếp",
  "Portfolio Model Components": "Thành phần mô hình portfolio",
  "Active Incidents": "Sự cố đang hoạt động",
  "View incidents": "Xem sự cố",
  "Open SOC Copilot": "Mở Trợ lý SOC",
  "Analyze critical alerts": "Phân tích cảnh báo nghiêm trọng",
  "Explain risk scoring": "Giải thích điểm rủi ro",
  "Recommend response actions": "Đề xuất hành động ứng phó",
  "Language & experience": "Ngôn ngữ & trải nghiệm",
  "Choose the interface language used on this device.": "Chọn ngôn ngữ giao diện trên thiết bị này.",
  English: "Tiếng Anh",
  Vietnamese: "Tiếng Việt",
  "Account & security": "Tài khoản & bảo mật",
  "Your public account is read-only to keep the shared demo safe.": "Tài khoản công khai chỉ có quyền xem để bảo vệ dữ liệu demo dùng chung.",
};

interface LanguageContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: (text: string) => string;
}

const LanguageContext = createContext<LanguageContextValue | null>(null);
const languageEvent = "cybersentinel:language-change";

function subscribeLanguage(callback: () => void) {
  window.addEventListener(languageEvent, callback);
  return () => window.removeEventListener(languageEvent, callback);
}

function getLanguageSnapshot(): Locale {
  return window.localStorage.getItem("cybersentinel-locale") === "vi" ? "vi" : "en";
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const locale = useSyncExternalStore<Locale>(
    subscribeLanguage,
    getLanguageSnapshot,
    (): Locale => "en",
  );
  const setLocale = (nextLocale: Locale) => {
    window.localStorage.setItem("cybersentinel-locale", nextLocale);
    window.dispatchEvent(new Event(languageEvent));
  };

  useEffect(() => {
    document.documentElement.lang = locale;
  }, [locale]);

  const value = useMemo<LanguageContextValue>(
    () => ({
      locale,
      setLocale,
      toggleLocale: () => setLocale(locale === "en" ? "vi" : "en"),
      t: (text) => (locale === "vi" ? (vi[text] ?? text) : text),
    }),
    [locale],
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useLanguage(): LanguageContextValue {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within LanguageProvider");
  }
  return context;
}
