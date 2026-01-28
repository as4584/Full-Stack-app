export default function EmptyCallsState() {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '3rem 1rem',
      textAlign: 'center',
      backgroundColor: '#f9fafb',
      borderRadius: '0.5rem',
      margin: '1rem 0'
    }}>
      <div style={{
        fontSize: '4rem',
        marginBottom: '1rem'
      }}>
        📞
      </div>
      <h3 style={{
        fontSize: '1.25rem',
        fontWeight: 600,
        marginBottom: '0.5rem',
        color: '#111827'
      }}>
        No calls yet
      </h3>
      <p style={{
        color: '#6b7280',
        marginBottom: '1.5rem',
        maxWidth: '400px'
      }}>
        Your recent calls will appear here once your AI receptionist starts handling incoming calls.
      </p>
      <button style={{
        padding: '0.75rem 1.5rem',
        backgroundColor: '#3d84ff',
        color: 'white',
        border: 'none',
        borderRadius: '0.5rem',
        cursor: 'pointer',
        fontSize: '0.875rem',
        fontWeight: 500
      }}>
        Configure Receptionist
      </button>
    </div>
  );
}
