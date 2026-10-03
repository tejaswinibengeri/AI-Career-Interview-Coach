import { useEffect, useState } from "react";
import api, { APIError, type AdminUserData } from "../../lib/api";

export default function AdminUsers() {
  const [users, setUsers] = useState<AdminUserData[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getAdminUsers();
      if (res.data) {
        setUsers(res.data);
      } else {
        setError("Failed to load users.");
      }
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError("Unable to connect to server.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRole = async (u: AdminUserData) => {
    const nextRole = u.role === "admin" ? "user" : "admin";
    try {
      const res = await api.updateAdminUserRole(u.id, { role: nextRole });
      if (res.data) {
        const updatedUser = res.data;
        setUsers((prev) => prev.map((item) => (item.id === u.id ? updatedUser : item)));
      }
    } catch {
      // Ignore error
    }
  };

  const handleToggleActive = async (u: AdminUserData) => {
    try {
      const res = await api.updateAdminUserRole(u.id, { is_active: !u.is_active });
      if (res.data) {
        const updatedUser = res.data;
        setUsers((prev) => prev.map((item) => (item.id === u.id ? updatedUser : item)));
      }
    } catch {
      // Ignore error
    }
  };


  const handleDeleteUser = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    try {
      await api.deleteAdminUser(id);
      setUsers(users.filter((u) => u.id !== id));
    } catch {
      // Ignore error
    }
  };

  const formatDate = (isoString: string) => {
    try {
      return new Date(isoString).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      });
    } catch {
      return isoString;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">User Management & Permissions</h2>
          <p className="text-xs text-surface-200/60">Privileged user role administration with candidate privacy protections</p>
        </div>
        <span className="text-xs text-surface-200/60 font-medium">Total Registered: {users.length}</span>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="space-y-3 animate-pulse">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-surface-900 rounded-2xl border border-white/5" />
          ))}
        </div>
      ) : (
        <div className="bg-surface-900 border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs text-surface-200">
              <thead className="bg-surface-800/80 text-surface-200 uppercase tracking-wider font-semibold border-b border-white/10">
                <tr>
                  <th className="px-6 py-4">User</th>
                  <th className="px-6 py-4">Role</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4">Joined</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {users.map((u) => (
                  <tr key={u.id} className="hover:bg-surface-800/40 transition-colors">
                    <td className="px-6 py-4 font-medium text-white">
                      <div>{u.name}</div>
                      <div className="text-[11px] text-surface-200/60 font-mono">{u.email}</div>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[10px] font-extrabold uppercase ${
                          u.role === "admin" || u.is_superuser
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            : "bg-surface-800 text-surface-200/60 border border-white/5"
                        }`}
                      >
                        {u.role === "admin" || u.is_superuser ? "👑 Admin" : "User"}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          u.is_active
                            ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                            : "bg-red-500/15 text-red-400 border border-red-500/30"
                        }`}
                      >
                        {u.is_active ? "Active" : "Deactivated"}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-surface-200/60">{formatDate(u.created_at)}</td>
                    <td className="px-6 py-4 text-right space-x-2">
                      <button
                        onClick={() => handleToggleRole(u)}
                        className="px-3 py-1 rounded-lg bg-surface-800 hover:bg-surface-700 text-white font-semibold cursor-pointer"
                      >
                        {u.role === "admin" ? "Demote" : "Promote to Admin"}
                      </button>
                      <button
                        onClick={() => handleToggleActive(u)}
                        className={`px-3 py-1 rounded-lg font-semibold cursor-pointer ${
                          u.is_active ? "bg-amber-500/15 text-amber-300 hover:bg-amber-500/25" : "bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25"
                        }`}
                      >
                        {u.is_active ? "Deactivate" : "Activate"}
                      </button>
                      <button
                        onClick={() => handleDeleteUser(u.id)}
                        className="px-3 py-1 rounded-lg bg-red-500/10 text-red-400 hover:bg-red-500/20 font-semibold cursor-pointer"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
