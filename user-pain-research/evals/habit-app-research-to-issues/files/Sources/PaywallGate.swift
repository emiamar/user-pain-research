import Foundation

/// Decides what free vs Pro users can see and do.
struct PaywallGate {
    static let freeHabitLimit = 3
    static let freeHistoryDays = 30

    let isPro: Bool

    func canAddHabit(currentCount: Int) -> Bool {
        isPro || currentCount < Self.freeHabitLimit
    }

    /// Check-ins older than `freeHistoryDays` are hidden for free users
    /// (they stay on disk but are not shown). If a Pro subscription lapses,
    /// older history disappears from view again.
    func visibleCheckIns(_ all: [CheckIn], now: Date = .now) -> [CheckIn] {
        guard !isPro else { return all }
        let cutoff = Calendar.current.date(byAdding: .day, value: -Self.freeHistoryDays, to: now)!
        return all.filter { $0.date >= cutoff }
    }

    /// CSV export is Pro-only. It locks again when the subscription lapses.
    static func canExportCSV(isPro: Bool) -> Bool {
        isPro
    }
}
