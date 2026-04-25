/* ============================================================
   Storage Module – Supabase Storage Integration
   ============================================================ */

const STORAGE_BUCKET = 'Map-files';

/**
 * Uploads a file to Supabase Storage via the backend endpoint.
 * The backend handles all Supabase operations securely.
 * 
 * Usage for alerts: called automatically with /alerts POST
 * Usage for profile: use uploadAvatarToStorage() instead
 */
async function uploadToStorage(file, featureName, itemId) {
  if (!file) return null;
  
  const user = Auth.getUser();
  if (!user) throw new Error("Must be logged in to upload files.");

  try {
    // Use FormData for file upload
    const fd = new FormData();
    fd.append('file', file);

    let endpoint = '/auth/avatar';
    let fileField = 'avatar';
    
    if (featureName === 'profile') {
      endpoint = '/auth/avatar';
      fileField = 'avatar';
    } else if (featureName === 'alerts') {
      endpoint = `/alerts/${itemId}/upload-image`;
      fileField = 'image';
    }

    fd.set(fileField, file); // Replace with correct field name
    
    // Upload via backend
    const res = await apiFetch(endpoint, {
      method: 'POST',
      body: fd
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'Upload failed');
    }

    const data = await res.json();
    return { path: data.avatar_url || data.image_url };

  } catch (error) {
    console.error("Storage upload error:", error);
    throw error;
  }
}

/**
 * Gets a signed URL for a file in the Map-files bucket.
 * Requests a signed URL from the backend.
 */
async function getSignedUrl(path, expiresIn = 3600) {
  if (!path) return null;

  // If it's already a full URL (external), return it as is
  if (path.startsWith('http')) {
    return { signedUrl: path };
  }

  try {
    const res = await apiFetch('/auth/signed-url', {
      method: 'POST',
      body: JSON.stringify({ file_path: path })
    });

    if (!res.ok) {
      console.warn("Could not get signed URL:", await res.text());
      // Return fallback for old format paths
      if (path.startsWith('/uploads/')) {
        return { signedUrl: path };
      }
      return null;
    }

    const data = await res.json();
    return { signedUrl: data.signed_url };

  } catch (error) {
    console.error("Error creating signed URL:", error);
    // Fallback for old local uploads
    if (path.startsWith('/uploads/')) {
      return { signedUrl: path };
    }
    return null;
  }
}

/**
 * Deletes a file from Supabase Storage via the backend.
 */
async function deleteFromStorage(path) {
  if (!path) return false;

  // Don't try to delete old local files
  if (path.startsWith('/uploads/') || path.startsWith('http')) {
    return false;
  }

  try {
    const res = await apiFetch('/auth/delete-file', {
      method: 'POST',
      body: JSON.stringify({ file_path: path })
    });

    if (!res.ok) {
      console.warn("Could not delete file from storage");
      return false;
    }

    return true;

  } catch (error) {
    console.error("Error deleting from storage:", error);
    return false;
  }
}

/**
 * Gets a signed URL for an alert image by alert ID.
 * Useful when you have the alert ID but not the file path.
 */
async function getAlertImageSignedUrl(alertId) {
  try {
    const res = await apiFetch(`/alerts/${alertId}/image-url`, {
      method: 'POST'
    });

    if (!res.ok) {
      console.warn("Could not get alert image signed URL");
      return null;
    }

    const data = await res.json();
    return { signedUrl: data.signed_url };

  } catch (error) {
    console.error("Error creating alert image signed URL:", error);
    return null;
  }
}
