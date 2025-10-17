# Work Schedule Module - Setup Guide

## Cài đặt Azure App Registration

### Bước 1: Tạo App Registration

1. Truy cập [Azure Portal](https://portal.azure.com)
2. Đi tới **Azure Active Directory** > **App registrations** > **New registration**
3. Điền thông tin:
   - **Name**: MoveGreen Work Schedule
   - **Supported account types**: Accounts in any organizational directory (Any Azure AD directory - Multitenant)
   - **Redirect URI**: Web - `https://greenmove.datcv.io.vn/auth/callback`

### Bước 2: Lấy thông tin cấu hình

Sau khi tạo xong, ghi lại:
- **Application (client) ID**
- **Directory (tenant) ID**

### Bước 3: Tạo Client Secret

1. Đi tới **Certificates & secrets** > **Client secrets** > **New client secret**
2. Mô tả: `Work Schedule API Secret`
3. Expires: 24 months
4. Ghi lại **Value** (chỉ hiện 1 lần)

### Bước 4: Cấu hình API Permissions

Đi tới **API permissions** > **Add a permission** > **Microsoft Graph** > **Application permissions**

**Cần thêm các permissions sau:**

#### Calendars permissions:
- `Calendars.Read` - Đọc lịch của tất cả người dùng
- `Calendars.ReadWrite` - Đọc và ghi lịch (nếu cần tạo/sửa events)

#### User permissions:
- `User.Read.All` - Đọc thông tin tất cả người dùng
- `User.ReadBasic.All` - Đọc thông tin cơ bản của người dùng

#### Directory permissions (optional):
- `Directory.Read.All` - Đọc thông tin directory

**⚠️ Quan trọng:** Sau khi thêm permissions, cần **Grant admin consent** cho tất cả permissions.

### Bước 5: Cập nhật cấu hình

Cập nhật file `src/config/config.ts`:

```typescript
MICROSOFT: {
  CLIENT_ID: 'your-application-client-id',
  CLIENT_SECRET: 'your-client-secret-value',
  TENANT_ID: 'your-directory-tenant-id',
  REDIRECT_URI: 'https://greenmove.datcv.io.vn/auth/callback',
  AUTHORITY: 'https://login.microsoftonline.com/common',
  GRAPH_API_URL: 'https://graph.microsoft.com/v1.0',
}
```

## Kiểm tra cấu hình

### Test 1: Kiểm tra access token

```bash
curl -X POST "https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&scope=https://graph.microsoft.com/.default"
```

**Expected Response:**
```json
{
  "token_type": "Bearer",
  "expires_in": 3599,
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsI..."
}
```

### Test 2: Kiểm tra Microsoft Graph API

```bash
curl -X GET "https://graph.microsoft.com/v1.0/users" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Test 3: Kiểm tra API của ứng dụng

```bash
curl -X GET "http://localhost:4869/work-schedule/events?fromDate=2024-01-01T00:00:00.000Z&toDate=2024-01-31T23:59:59.000Z" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Xử lý lỗi phổ biến

### 1. "invalid_client" error
- **Nguyên nhân**: Client ID hoặc Client Secret sai
- **Giải pháp**: Kiểm tra lại thông tin trong Azure Portal và config

### 2. "insufficient_privileges" error  
- **Nguyên nhân**: Chưa grant admin consent cho permissions
- **Giải pháp**: Đi tới API permissions > Grant admin consent

### 3. "Forbidden" khi truy cập calendar
- **Nguyên nhân**: Thiếu permission `Calendars.Read`
- **Giải pháp**: Thêm permission và grant admin consent

### 4. "User not found"
- **Nguyên nhân**: Microsoft ID trong database không đúng
- **Giải pháp**: Kiểm tra quá trình đăng nhập Microsoft có lưu đúng ID

## Production Checklist

### Security
- [ ] Lưu trữ Client Secret an toàn (environment variables)
- [ ] Sử dụng HTTPS cho redirect URI
- [ ] Enable audit logs trong Azure AD
- [ ] Thiết lập conditional access policies

### Monitoring
- [ ] Monitor API call rates để tránh throttling
- [ ] Setup alerting cho authentication failures
- [ ] Log các requests để debugging

### Performance
- [ ] Implement caching cho access tokens (reuse trong 1 giờ)
- [ ] Limit số events trả về (khuyến nghị max 250/request)
- [ ] Sử dụng pagination cho kết quả lớn

### Compliance
- [ ] Đảm bảo permissions tối thiểu (principle of least privilege)
- [ ] Document data usage và retention policies
- [ ] Comply với organizational data governance

## Environment Variables

Tạo file `.env` hoặc cập nhật environment:

```env
# Microsoft Graph API
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT_ID=your-tenant-id
MICROSOFT_REDIRECT_URI=https://greenmove.datcv.io.vn/auth/callback

# Database
DATABASE_HOST=localhost
DATABASE_PORT=5445
DATABASE_USER=your-db-user
DATABASE_PASSWORD=your-db-password
DATABASE_NAME=vmg

# JWT
JWT_SECRET=your-jwt-secret
```

## Rate Limits

Microsoft Graph API có rate limits:
- **Application permissions**: 10,000 requests per 10 minutes per application
- **Delegated permissions**: 10,000 requests per 10 minutes per user

Module tự động handle rate limiting và retry failed requests.

## Troubleshooting Commands

```bash
# Check if app is running
curl -X GET "http://localhost:4869/health"

# Check database connection
npm run typeorm:connection

# Check Microsoft Graph connectivity
node -e "
const axios = require('axios');
axios.post('https://login.microsoftonline.com/YOUR_TENANT_ID/oauth2/v2.0/token', 
  'grant_type=client_credentials&client_id=YOUR_CLIENT_ID&client_secret=YOUR_CLIENT_SECRET&scope=https://graph.microsoft.com/.default',
  { headers: { 'Content-Type': 'application/x-www-form-urlencoded' } }
).then(r => console.log('✅ Microsoft auth OK')).catch(e => console.log('❌ Microsoft auth failed:', e.message));
"

# Test work schedule API
curl -X GET "http://localhost:4869/work-schedule/events?fromDate=2024-01-01T00:00:00.000Z&toDate=2024-01-07T23:59:59.000Z" \
  -H "Authorization: Bearer $(node -e "console.log(require('jsonwebtoken').sign({userId:'test'}, 'your-jwt-secret'))")"
```
