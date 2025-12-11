# Multi-Platform SSO Implementation Guide

This guide provides best practices for implementing SSO across mobile (Android/iOS) and web applications using the ARGA SSO Service v2.

---

## Architecture Overview

The ARGA SSO system supports multiple authentication flows optimized for different platforms:

- **Mobile Native Apps**: JSON API responses with deep link redirects
- **Web SPAs**: JSON API responses with frontend routing
- **Web Traditional**: Backend redirects (optional)
- **Backend Services**: gRPC API for user data access

---

## Authentication Flows by Platform

### 1. Mobile Native Apps (Android/iOS)

#### First-Time Login Flow

```
User opens HRIS Mobile App
  ↓
App checks for stored tokens (Keychain/Keystore)
  ↓ (none found)
App opens SSO login page in WebView/Browser
  URL: https://sso.arga.com/login?client_id=hris&redirect_uri=hrisapp://callback
  ↓
User authenticates (email/Google/Firebase)
  ↓
Backend validates credentials
  ↓
Backend returns JSON response:
  {
    "sso_token": "...",
    "access_token": "...",
    "refresh_token": "...",
    "device_id": "...",
    "expires_in": 1800
  }
  ↓
WebView/Browser captures response
  ↓
App stores tokens securely:
  - iOS: Keychain
  - Android: EncryptedSharedPreferences
  ↓
App navigates to home screen
```

#### API Endpoints for Mobile

**Login with Email:**
```http
POST /api/v1/auth/login/email
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "client_id": "hris",
  "device_info": {
    "device_name": "iPhone 14 Pro",
    "os": "iOS 17.1",
    "app_version": "1.2.0"
  },
  "fcm_token": "fcm_device_token_here"
}

Response:
{
  "error": false,
  "message": "Login berhasil",
  "data": {
    "sso_token": "eyJ...",
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "bearer",
    "expires_in": 1800,
    "user": { ... }
  }
}
```

**Login with Firebase (Google/Apple/Phone):**
```http
POST /api/v1/auth/login/firebase
Content-Type: application/json

{
  "firebase_token": "firebase_id_token_from_sdk",
  "client_id": "hris",
  "device_info": { ... },
  "fcm_token": "..."
}
```

#### Token Storage (Mobile)

**iOS (Swift):**
```swift
import Security

class SecureStorage {
    func saveToken(key: String, value: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecValueData as String: value.data(using: .utf8)!,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock
        ]
        SecItemDelete(query as CFDictionary)
        SecItemAdd(query as CFDictionary, nil)
    }

    func getToken(key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true
        ]
        var result: AnyObject?
        SecItemCopyMatching(query as CFDictionary, &result)

        if let data = result as? Data {
            return String(data: data, encoding: .utf8)
        }
        return nil
    }
}

// Usage
let storage = SecureStorage()
storage.saveToken(key: "access_token", value: accessToken)
storage.saveToken(key: "refresh_token", value: refreshToken)
storage.saveToken(key: "sso_token", value: ssoToken)
storage.saveToken(key: "device_id", value: deviceId)
```

**Android (Kotlin):**
```kotlin
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecureStorage(context: Context) {
    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val sharedPreferences = EncryptedSharedPreferences.create(
        context,
        "secure_prefs",
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )

    fun saveToken(key: String, value: String) {
        sharedPreferences.edit().putString(key, value).apply()
    }

    fun getToken(key: String): String? {
        return sharedPreferences.getString(key, null)
    }
}

// Usage
val storage = SecureStorage(context)
storage.saveToken("access_token", accessToken)
storage.saveToken("refresh_token", refreshToken)
storage.saveToken("sso_token", ssoToken)
storage.saveToken("device_id", deviceId)
```

#### Deep Link Configuration

**iOS (Info.plist):**
```xml
<key>CFBundleURLTypes</key>
<array>
    <dict>
        <key>CFBundleURLSchemes</key>
        <array>
            <string>hrisapp</string>
        </array>
        <key>CFBundleURLName</key>
        <string>com.arga.hris</string>
    </dict>
</array>
```

**Android (AndroidManifest.xml):**
```xml
<activity android:name=".MainActivity">
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data
            android:scheme="hrisapp"
            android:host="callback" />
    </intent-filter>
</activity>
```

#### Silent Token Refresh

Implement automatic token refresh before expiration:

```swift
// iOS
class TokenManager {
    private let storage = SecureStorage()
    private var refreshTask: Task<Void, Never>?

    func startAutoRefresh() {
        refreshTask = Task {
            while !Task.isCancelled {
                // Refresh 5 minutes before expiration
                try? await Task.sleep(nanoseconds: 25 * 60 * 1_000_000_000)
                await refreshTokenIfNeeded()
            }
        }
    }

    func refreshTokenIfNeeded() async {
        guard let refreshToken = storage.getToken(key: "refresh_token"),
              let deviceId = storage.getToken(key: "device_id") else {
            return
        }

        let response = try? await API.post("/auth/refresh", body: [
            "refresh_token": refreshToken,
            "device_id": deviceId
        ])

        if let newAccessToken = response?["access_token"],
           let newRefreshToken = response?["refresh_token"] {
            storage.saveToken(key: "access_token", value: newAccessToken)
            storage.saveToken(key: "refresh_token", value: newRefreshToken)
        }
    }
}
```

---

### 2. Web Single Page Applications (React/Vue/Angular)

#### Authentication Flow

```
User visits HRIS Web App (https://hris.arga.com)
  ↓
App checks localStorage for tokens
  ↓ (none found)
App redirects to SSO login page
  URL: https://sso.arga.com/login?client_id=hris&redirect_uri=https://hris.arga.com/callback
  ↓
User authenticates at SSO page
  ↓
SSO frontend calls login API
  ↓
SSO frontend receives tokens in JSON response
  ↓
SSO frontend redirects to redirect_uri with tokens:
  Method 1: URL hash fragment (more secure)
    https://hris.arga.com/callback#access_token=...&refresh_token=...
  Method 2: postMessage (if in iframe)
  ↓
HRIS app extracts tokens from URL/message
  ↓
HRIS stores tokens:
  - access_token → sessionStorage or memory
  - refresh_token → localStorage or httpOnly cookie
  - sso_token → localStorage (for cross-app SSO)
  ↓
HRIS clears tokens from URL (security)
  ↓
HRIS redirects to dashboard
```

#### React Example

**Authentication Context:**
```javascript
// contexts/AuthContext.jsx
import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [accessToken, setAccessToken] = useState(null);
  const [loading, setLoading] = useState(true);

  const API_BASE = 'https://sso.arga.com/api/v1';
  const CLIENT_ID = 'hris';

  // Load tokens from storage on mount
  useEffect(() => {
    const storedAccessToken = sessionStorage.getItem('access_token');
    const storedRefreshToken = localStorage.getItem('refresh_token');
    const storedDeviceId = localStorage.getItem('device_id');

    if (storedAccessToken) {
      setAccessToken(storedAccessToken);
      verifyToken(storedAccessToken);
    } else if (storedRefreshToken && storedDeviceId) {
      refreshToken(storedRefreshToken, storedDeviceId);
    } else {
      setLoading(false);
    }
  }, []);

  // Auto-refresh token before expiration
  useEffect(() => {
    if (!accessToken) return;

    // Refresh 5 minutes before expiration (25 min for 30 min tokens)
    const refreshInterval = setInterval(() => {
      const refreshToken = localStorage.getItem('refresh_token');
      const deviceId = localStorage.getItem('device_id');
      if (refreshToken && deviceId) {
        refreshToken(refreshToken, deviceId);
      }
    }, 25 * 60 * 1000);

    return () => clearInterval(refreshInterval);
  }, [accessToken]);

  const verifyToken = async (token) => {
    try {
      const response = await axios.get(`${API_BASE}/auth/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data.data);
    } catch (error) {
      console.error('Token verification failed:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const refreshToken = async (refreshToken, deviceId) => {
    try {
      const response = await axios.post(`${API_BASE}/auth/refresh`, {
        refresh_token: refreshToken,
        device_id: deviceId
      });

      const { access_token, refresh_token: newRefreshToken } = response.data.data;

      sessionStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', newRefreshToken);
      setAccessToken(access_token);

      verifyToken(access_token);
    } catch (error) {
      console.error('Token refresh failed:', error);
      logout();
    }
  };

  const login = async (email, password) => {
    const deviceInfo = {
      device_name: navigator.userAgent,
      os: navigator.platform,
      browser: navigator.appVersion
    };

    const response = await axios.post(`${API_BASE}/auth/login/email`, {
      email,
      password,
      client_id: CLIENT_ID,
      device_info: deviceInfo
    });

    const {
      access_token,
      refresh_token,
      sso_token,
      user
    } = response.data.data;

    // Store tokens
    sessionStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    localStorage.setItem('sso_token', sso_token);
    localStorage.setItem('device_id', user.device_id);

    setAccessToken(access_token);
    setUser(user);

    return user;
  };

  const logout = async () => {
    try {
      if (accessToken) {
        await axios.post(
          `${API_BASE}/auth/logout`,
          {},
          { headers: { Authorization: `Bearer ${accessToken}` } }
        );
      }
    } catch (error) {
      console.error('Logout API failed:', error);
    }

    // Clear local storage
    sessionStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('sso_token');
    localStorage.removeItem('device_id');

    setAccessToken(null);
    setUser(null);
  };

  const value = {
    user,
    accessToken,
    loading,
    login,
    logout,
    isAuthenticated: !!user
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
```

**Axios Interceptor for Auto Token Refresh:**
```javascript
// utils/axios.js
import axios from 'axios';

const api = axios.create({
  baseURL: 'https://sso.arga.com/api/v1'
});

// Request interceptor - add token
api.interceptors.request.use(
  (config) => {
    const token = sessionStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 and refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      const refreshToken = localStorage.getItem('refresh_token');
      const deviceId = localStorage.getItem('device_id');

      if (refreshToken && deviceId) {
        try {
          const response = await axios.post('/auth/refresh', {
            refresh_token: refreshToken,
            device_id: deviceId
          });

          const { access_token, refresh_token: newRefreshToken } = response.data.data;

          sessionStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', newRefreshToken);

          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        } catch (refreshError) {
          // Refresh failed, redirect to login
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;
```

#### Token Storage Strategy for Web

| Token Type | Storage Location | Reasoning |
|------------|------------------|-----------|
| `access_token` | sessionStorage or memory | Short-lived, cleared on tab close |
| `refresh_token` | localStorage or httpOnly cookie | Long-lived, persists across sessions |
| `sso_token` | localStorage | Shared across tabs for SSO |
| `device_id` | localStorage | Needed for refresh |

**Most Secure Option: httpOnly Cookies**

For production web apps, consider using httpOnly cookies for refresh tokens:

1. Backend sets httpOnly cookie on login
2. Frontend never has access to refresh token
3. Refresh endpoint automatically uses cookie
4. Prevents XSS attacks from stealing refresh tokens

---

### 3. Cross-App SSO (Second App Login)

When a user who is already logged into App A opens App B:

```
User opens Finance App (already logged into HRIS)
  ↓
Finance App checks localStorage for tokens
  ↓ (none found for Finance)
Finance App checks for SSO token
  ↓ (found!)
Finance App calls token exchange API:
  POST /api/v1/auth/exchange
  {
    "sso_token": "...",
    "client_id": "finance",
    "device_info": {...}
  }
  ↓
Backend validates SSO token and user access
  ↓
Backend returns app-specific tokens:
  {
    "access_token": "...",  // for Finance app
    "refresh_token": "...", // for Finance app
    "sso_token": "...",     // same SSO token
    "user": {...}
  }
  ↓
Finance App stores tokens
  ↓
User is logged in WITHOUT typing credentials! ✨
```

**Implementation:**
```javascript
// Check for SSO session on app load
const checkSSOSession = async () => {
  const ssoToken = localStorage.getItem('sso_token');

  if (ssoToken) {
    try {
      const response = await axios.post('/auth/exchange', {
        sso_token: ssoToken,
        client_id: 'finance',
        device_info: getDeviceInfo()
      });

      const { access_token, refresh_token } = response.data.data;

      sessionStorage.setItem('access_token', access_token);
      localStorage.setItem('refresh_token', refresh_token);

      return true; // SSO successful
    } catch (error) {
      console.error('SSO exchange failed:', error);
      localStorage.removeItem('sso_token'); // Invalid SSO token
      return false;
    }
  }

  return false; // No SSO token
};
```

---

### 4. Backend Services (Service-to-Service)

For backend microservices that need user data:

**Option 1: gRPC (Already Implemented)**

```python
# From another Python service
import grpc
from proto.sso import user_pb2, user_pb2_grpc

channel = grpc.insecure_channel('sso.arga.com:50051')
stub = user_pb2_grpc.UserServiceStub(channel)

# Get user by ID
request = user_pb2.GetUserRequest(user_id=user_id)
response = stub.GetUser(request)

if response.found:
    user = response.user
    print(f"User: {user.name}, Email: {user.email}")
```

**Option 2: REST API Token Validation**

Add endpoint for service-to-service token validation:

```python
# Add to app/modules/auth/routers/auth.py

@router.post(
    "/validate",
    response_model=DataResponse[UserData],
    summary="Validate access token (for backend services)"
)
async def validate_token(
    auth_service: AuthServiceDep,
    authorization: str = Header(..., description="Bearer token")
) -> DataResponse[UserData]:
    """
    Validate JWT access token and return user data.
    For use by backend services.
    """
    if not authorization.startswith("Bearer "):
        raise UnauthorizedException("Invalid authorization header")

    token = authorization[7:]  # Remove "Bearer "
    user_data = await auth_service.verify_access_token(token)

    return DataResponse(
        error=False,
        message="Token valid",
        data=user_data
    )
```

Usage from Node.js service:
```javascript
const axios = require('axios');

async function validateToken(accessToken) {
  try {
    const response = await axios.post(
      'https://sso.arga.com/api/v1/auth/validate',
      {},
      { headers: { Authorization: `Bearer ${accessToken}` } }
    );

    return response.data.data; // User data
  } catch (error) {
    throw new Error('Invalid token');
  }
}
```

---

## Session Management

### Global Logout (All Apps, All Devices)

```http
POST /api/v1/auth/logout
Authorization: Bearer {access_token}

Response: 200 OK
```

This logs out the user from:
- All client applications
- All devices
- Clears SSO session

### Client-Specific Logout

```http
POST /api/v1/auth/logout/client
Authorization: Bearer {access_token}
X-Client-ID: hris

Response: 200 OK
```

Logs out only from HRIS app (all devices).

### Device-Specific Logout

```http
POST /api/v1/auth/logout/client
Authorization: Bearer {access_token}
X-Client-ID: hris
X-Device-ID: device_uuid_here

Response: 200 OK
```

Logs out only from HRIS app on specific device.

### View Active Sessions

```http
GET /api/v1/auth/sessions
Authorization: Bearer {access_token}

Response:
{
  "error": false,
  "message": "Ditemukan 3 sesi aktif di 2 aplikasi",
  "data": {
    "sessions": {
      "hris": [
        {
          "device_id": "...",
          "device_info": {"device_name": "iPhone 13", "os": "iOS 16"},
          "ip_address": "192.168.1.100",
          "created_at": "2024-01-15T10:30:00Z",
          "last_activity": "2024-01-15T14:30:00Z"
        }
      ],
      "finance": [...]
    },
    "total_clients": 2,
    "total_sessions": 3
  }
}
```

---

## Security Best Practices

### 1. Token Expiration

| Token Type | Recommended TTL | Configurable In |
|------------|-----------------|-----------------|
| Access Token | 15-30 minutes | `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Refresh Token | 30-60 days | `REFRESH_TOKEN_EXPIRE_DAYS` |
| SSO Token | Same as refresh token | `REFRESH_TOKEN_EXPIRE_DAYS` |

### 2. HTTPS Only

**Always use HTTPS in production.** Tokens sent over HTTP can be intercepted.

### 3. CORS Configuration

Update `settings.py` with your app domains:

```python
CORS_ORIGINS: List[str] = [
    "https://hris.arga.com",
    "https://finance.arga.com",
    "https://portal.arga.com",
    # Development
    "http://localhost:3000",
    "http://localhost:8080",
]
```

### 4. Secure Token Storage

| Platform | Recommended Storage | Security Level |
|----------|---------------------|----------------|
| iOS | Keychain | 🔒🔒🔒 High |
| Android | EncryptedSharedPreferences | 🔒🔒🔒 High |
| Web (access) | sessionStorage or memory | 🔒🔒 Medium |
| Web (refresh) | httpOnly cookie | 🔒🔒🔒 High |
| Web (refresh alt) | localStorage | 🔒 Low (XSS risk) |

### 5. FCM Push Notifications

Store FCM tokens during login to enable:
- Force logout notifications
- Session expiration warnings
- Security alerts

### 6. Rate Limiting

Implement rate limiting on auth endpoints:
- Login: 5 attempts per 15 minutes per IP
- Refresh: 10 attempts per minute per user
- Exchange: 20 attempts per minute per user

---

## Recommended Application Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    ARGA SSO Service v2                   │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ REST API │  │ gRPC API │  │  Redis   │             │
│  │ (FastAPI)│  │  (User   │  │(Sessions)│             │
│  │          │  │   Data)  │  │          │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │              │                    │
│  ┌────┴─────────────┴──────────────┴─────┐             │
│  │         PostgreSQL (Users, Apps)       │             │
│  └────────────────────────────────────────┘             │
└───────────────────┬──────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌───▼─────┐
   │ HRIS    │ │Finance │ │ Portal  │
   │ Web/iOS │ │  Web   │ │  Web    │
   │ Android │ │        │ │         │
   └─────────┘ └────────┘ └─────────┘

   Each app:
   - Stores app-specific tokens locally
   - Shares SSO token (localStorage/Keychain)
   - Auto-exchanges on first open if SSO exists
   - Refreshes tokens automatically
   - Syncs logout across tabs (web) or via push (mobile)
```

---

## Troubleshooting

### Issue: User can't access app after login

**Check:**
1. Is the app registered in `applications` table?
2. Does user have access? Check `user_applications` table
3. Is app active? Check `applications.is_active`

### Issue: Token refresh fails

**Check:**
1. Is `device_id` correct?
2. Is `client_id` in token payload matching request?
3. Is refresh token expired? Check `REFRESH_TOKEN_EXPIRE_DAYS`
4. Is Redis session still valid?

### Issue: Cross-app SSO doesn't work

**Check:**
1. Is `sso_token` being stored in shared location? (localStorage for web, Keychain/Keystore for mobile)
2. Is SSO session still valid in Redis?
3. Does user have access to the target app?

---

## Monitoring & Observability

### Key Metrics to Track

1. **Authentication Success Rate**
   - Login success vs failures
   - By provider (email, Google, Firebase)

2. **Session Duration**
   - Average session length
   - Sessions per user per app

3. **Token Refresh Rate**
   - Refresh requests per minute
   - Refresh failures

4. **Cross-App SSO Usage**
   - Exchange requests
   - SSO success rate

5. **Active Sessions**
   - Total active sessions
   - By app and by user

### Logging Best Practices

Already implemented in the codebase:
- Auth attempts logged with user email and client_id
- Failed logins logged with reason
- Token exchanges logged
- Session creation/deletion logged

Monitor these logs for:
- Unusual login patterns
- Failed authentication spikes
- Token abuse

---

## Summary

For a multi-platform SSO system supporting mobile and web:

✅ **Use JSON APIs for all platforms** (current implementation is correct)
✅ **Platform-specific token storage** (Keychain, EncryptedSharedPreferences, sessionStorage/httpOnly cookies)
✅ **Automatic token refresh** before expiration
✅ **Cross-app SSO** via token exchange with shared SSO token
✅ **Session management** with granular logout options
✅ **Secure defaults** (HTTPS, short-lived access tokens, long-lived refresh tokens)
✅ **gRPC API** for backend service-to-service communication

The current ARGA SSO v2 architecture already supports all of these patterns effectively!
