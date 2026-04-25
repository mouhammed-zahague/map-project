# Supabase Storage Integration Guide

## ✅ What Has Been Implemented

This integration connects all file uploads in your Green Campus Alert application to **Supabase Storage** using the private "Map-files" bucket. Every uploaded file is stored with a clean folder structure and secured with access rules.

### Upload Features Connected

#### 1. **Alert Image Uploads** ✅
- **Endpoint**: `POST /api/alerts` (when creating new alerts with image)
- **Feature**: Users can upload a photo with their alert report
- **Path Structure**: `${userId}/alerts/${alertId}/${uuid}.${ext}`
- **Frontend**: Reports modal with drag-and-drop and preview
- **Display**: Uses signed URLs (1-hour expiry) for secure viewing

#### 2. **User Avatar Uploads** ✅
- **Endpoint**: `POST /api/auth/avatar`
- **Feature**: Users can upload their profile picture
- **Path Structure**: `${userId}/profile/${uuid}.${ext}`
- **Delete**: `DELETE /api/auth/avatar`
- **Display**: Uses signed URLs from backend

#### 3. **Alert Image Updates** ✅
- **Endpoint**: `POST /api/alerts/{id}/upload-image`
- **Feature**: Update/replace image for existing alerts (owner only)
- **Old File**: Automatically deleted when replacing
- **Access Control**: Only alert owner or admin can update

#### 4. **File Deletion** ✅
- **Alert images**: Automatically deleted when alert is deleted
- **Avatars**: Can be deleted via `DELETE /api/auth/avatar`
- **Generic endpoint**: `POST /api/auth/delete-file` (for any user-owned file)

### API Endpoints

#### Alert Operations
```
POST   /api/alerts                    - Create alert with image
GET    /api/alerts/{id}               - Get alert details
POST   /api/alerts/{id}/image-url    - Get signed URL for alert image
POST   /api/alerts/{id}/upload-image - Update alert image
DELETE /api/alerts/{id}               - Delete alert (removes file too)
```

#### User/Profile Operations
```
POST   /api/auth/avatar               - Upload/replace avatar
DELETE /api/auth/avatar               - Delete avatar
POST   /api/auth/signed-url          - Get signed URL for any file
POST   /api/auth/delete-file         - Delete any user-owned file
```

### Folder Structure in Supabase Storage

```
Map-files/
├── {userId}/
│   ├── alerts/
│   │   ├── {alertId}/
│   │   │   ├── {uuid1}.jpg
│   │   │   └── {uuid2}.png
│   │   └── ...
│   └── profile/
│       ├── {uuid}.jpg  (avatar)
│       └── ...
├── {anotherUserId}/
│   └── ...
```

---

## 🔧 Setup Instructions

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs the new `supabase` package (version 2.1.4).

### 2. Environment Variables

Add these to your `.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key
SUPABASE_STORAGE_BUCKET=Map-files

# Existing variables (keep these)
DB_USER=root
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=green_campus_db
JWT_SECRET_KEY=your-jwt-secret
SECRET_KEY=your-secret-key
```

**How to get SUPABASE_URL and SUPABASE_KEY:**
1. Go to your Supabase project dashboard
2. Settings → API
3. Copy "Project URL" → SUPABASE_URL
4. Copy "anon/public" key → SUPABASE_KEY

### 3. Verify Supabase Bucket Security Policies

Your bucket policies should allow each user to only access their own folder:

```sql
-- Storage bucket RLS policy example
CREATE POLICY "Users can upload to their own folder"
ON storage.objects FOR INSERT
WITH CHECK (
  (auth.uid())::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can read their own files"
ON storage.objects FOR SELECT
USING (
  (auth.uid())::text = (storage.foldername(name))[1]
);

CREATE POLICY "Users can delete their own files"
ON storage.objects FOR DELETE
USING (
  (auth.uid())::text = (storage.foldername(name))[1]
);
```

---

## 📋 File Changes Summary

### Backend Files Modified

| File | Changes |
|------|---------|
| [backend/config.py](backend/config.py) | Added Supabase configuration variables |
| [backend/requirements.txt](backend/requirements.txt) | Added `supabase==2.1.4` |
| **backend/supabase_storage.py** | **NEW** - Storage manager class |
| [backend/routes/alerts.py](backend/routes/alerts.py) | Updated alert creation and deletion, added image endpoints |
| [backend/routes/auth.py](backend/routes/auth.py) | Added avatar upload/delete, signed URL, file delete endpoints |

### Frontend Files Modified

| File | Changes |
|------|---------|
| [frontend/js/storage.js](frontend/js/storage.js) | Updated to use backend endpoints instead of direct Supabase calls |
| [frontend/js/map.js](frontend/js/map.js) | Added `openAlertDetail()` function with signed URL support |

### New Backend Module

**[backend/supabase_storage.py](backend/supabase_storage.py)**
- `SupabaseStorageManager` class
- Methods: `upload_file()`, `delete_file()`, `get_signed_url()`
- Singleton pattern: `get_storage_manager()`

---

## 🚀 How It Works

### Alert Creation with Image

1. User uploads image in report form
2. Form submitted to `POST /api/alerts` with multipart/form-data
3. Backend:
   - Creates alert in database
   - Gets alert ID from database
   - Uploads image to Supabase: `{userId}/alerts/{alertId}/{uuid}.jpg`
   - Saves path in `alerts.image_url`
4. Response returns alert with file path stored

### Displaying Alert Image

1. Frontend fetches alert details via `GET /api/alerts/{id}`
2. If `alert.image_url` exists, calls `POST /api/alerts/{id}/image-url`
3. Backend generates signed URL (1-hour expiry)
4. Frontend displays image using signed URL
5. URL expires after 1 hour (user can get new one by viewing alert again)

### User Avatar Upload

1. User clicks "Upload Avatar" button
2. File sent to `POST /api/auth/avatar`
3. Backend:
   - Deletes old avatar if exists
   - Uploads new to Supabase: `{userId}/profile/{uuid}.jpg`
   - Saves path in `users.avatar_url`
4. Returns new avatar URL

### File Deletion

**When deleting an alert:**
- Alert image file removed from Supabase automatically
- Alert record removed from database

**When deleting avatar:**
- User calls `DELETE /api/auth/avatar`
- Avatar file removed from Supabase
- `users.avatar_url` set to NULL

---

## 🔐 Security

### Path-Based Access Control
- Every file path starts with `{userId}` from JWT token
- Backend verifies user owns the file before operations
- Users cannot access or delete other users' files

### Signed URLs
- Private bucket requires signed URLs to view files
- URL expires after 1 hour (prevents long-term sharing)
- Backend generates URLs only for authorized users

### JWT Authentication
- All upload/delete endpoints require `@jwt_required()`
- User ID extracted from JWT token
- Operations scoped to current user

---

## ⚙️ Configuration Details

### File Upload Limits
```python
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
```

### Signed URL Expiry
```python
SIGNED_URL_EXPIRY = 3600  # 1 hour
```

Adjust in [backend/config.py](backend/config.py) if needed.

---

## 📝 Database Model Changes

### No Migration Needed ✅
The existing database schema already supports this integration:

- `users.avatar_url` (VARCHAR 255) - stores file path
- `alerts.image_url` (VARCHAR 255) - stores file path
- `alert_images` table ready for future multiple-images feature

File paths are stored as:
```
123/profile/550e8400-e29b-41d4-a716-446655440000.jpg
123/alerts/456/5f9c4ab0-8a7e-4f5d-9c3e-b0a7f4d9e8c1.png
```

---

## 🧪 Testing Checklist

### Alert Upload
- [ ] Create alert with image → file uploaded to Supabase
- [ ] Open alert details → image displays with signed URL
- [ ] Check `alerts.image_url` in database
- [ ] Verify file in Supabase Storage bucket
- [ ] Delete alert → file removed from Supabase

### Avatar Upload
- [ ] POST `/api/auth/avatar` with image
- [ ] Check `users.avatar_url` in database
- [ ] Verify file path format: `{userId}/profile/{uuid}.ext`
- [ ] GET `/api/auth/me` shows avatar_url
- [ ] DELETE `/api/auth/avatar` removes file
- [ ] Check old avatar deleted from Supabase

### Signed URL
- [ ] POST `/api/auth/signed-url` with valid file path
- [ ] Response contains valid signed URL
- [ ] URL accessible for 1 hour
- [ ] URL expires after 1 hour
- [ ] Try with non-owned file → returns 403

### Security
- [ ] Cannot delete other user's files
- [ ] Cannot get signed URL for other user's files
- [ ] Verify JWT token required on all endpoints
- [ ] Test with missing file path → returns 400

---

## 🐛 Troubleshooting

### "SUPABASE_URL and SUPABASE_KEY must be set"
- Check `.env` file has both variables
- Verify they're correct from Supabase dashboard
- Restart backend: `python -m flask run`

### "File extension not allowed"
- Check file extension in `ALLOWED_EXTENSIONS`
- Allowed: png, jpg, jpeg, gif, webp, pdf, doc, docx
- Update in [backend/config.py](backend/config.py) if needed

### "Unauthorized" error on file operations
- Verify JWT token is being sent
- Check user ID in token matches file path owner
- Ensure user is logged in

### Image not displaying
- Check `alerts.image_url` has correct path
- Verify file exists in Supabase bucket
- Call `/api/alerts/{id}/image-url` to get fresh signed URL
- Check browser console for CORS errors

### "Module 'supabase' not found"
- Run: `pip install supabase==2.1.4`
- Ensure using correct Python environment
- Verify `requirements.txt` was updated

---

## 📚 Related Documentation

- [Supabase Storage Docs](https://supabase.com/docs/guides/storage)
- [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [Your Project Database Schema](../database/schema.sql)
- [API Documentation](../docs/api_documentation.md)

---

## 🎯 Next Steps (Optional Enhancements)

### Already Ready in Database
- [ ] Implement multiple images per alert (use `alert_images` table)
- [ ] Add image cropping/editing before upload
- [ ] Implement thumbnail generation

### Future Features
- [ ] Rate limiting on uploads
- [ ] Virus scanning for uploaded files
- [ ] Per-user storage quotas
- [ ] Image compression on upload
- [ ] Drag-and-drop for multiple files

---

**Implementation Date**: April 2026  
**Integration**: Supabase Storage + Flask Backend + Web Frontend
