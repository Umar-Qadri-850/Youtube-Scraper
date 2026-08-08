YouTube Latest Video & Transcript Scraper

A YouTube scraper that accepts a YouTube channel name or channel URL, automatically finds the latest video uploaded by that channel, and extracts its transcript along with complete video metadata.

The scraper returns the results in a clean and structured JSON format, making it easy to integrate with AI applications, translation systems, content monitoring tools, and other automated workflows.

Features
Accepts a YouTube channel URL
Automatically finds the latest uploaded video
Extracts complete video metadata
Retrieves the available video transcript
Supports auto-generated transcripts
Detects the transcript language
Returns available transcript languages
Returns transcript timestamps
Returns structured JSON output
Useful for AI summarization and translation pipelines
Input

Provide a YouTube channel URL, for example:

https://www.youtube.com/@geonews
JSON Response

Example response:

{
  "status": "success",
  "channel_url": "https://www.youtube.com/@geonews",
  "video_id": "jgItrm_9ZCo",
  "title": "“Jamaat-e-Islami Protest Shuts Down Karachi: What’s Behind the Movement?” | Breaking News | Geo News",
  "url": "https://www.youtube.com/watch?v=jgItrm_9ZCo",
  "channel_name": "Geo News",
  "channel_username": "geonews",
  "published_at": "2026-08-07T16:22:23Z",
  "view_count": 433,
  "like_count": 6,
  "comment_count": 0,
  "duration_seconds": 90,
  "description": "#JamaatEIslami #KarachiProtest #KarachiShutdown #PakistanPolitics #JIProtest #KarachiNews #PakistanNews #PoliticalProtest #CurrentAffairs #BreakingNews",
  "thumbnail": "https://i.ytimg.com/vi/jgItrm_9ZCo/hqdefault.jpg",
  "selected_language": "Hindi (auto-generated)",
  "is_auto_generated": true,
  "available_languages": [
    "Hindi (auto-generated)"
  ],
  "transcript": [
    {
      "start": 0.64,
      "duration": 3.0,
      "text": "दो"
    }
  ]
}
Transcript Format

Each transcript entry contains the timestamp and corresponding text:

{
  "start": 0.64,
  "duration": 3.0,
  "text": "दो"
}

Where:

start is the starting time of the transcript segment in seconds.
duration is the duration of the segment in seconds.
text is the spoken text.
Workflow
YouTube Channel
      |
      v
Find Latest Video
      |
      v
Extract Video Metadata
      |
      v
Find Available Transcript
      |
      v
Extract Transcript
      |
      v
Return Structured JSON
Use Cases

This scraper can be used for:

YouTube news monitoring
AI-powered video summarization
Automatic translation
News aggregation
Content analysis
Transcript processing
AI chatbots
Automated content pipelines
Monitoring the latest videos from specific YouTube channels
Future Integration

The transcript can be passed to a translation service to convert content from one language to another, for example:

Hindi Transcript
      |
      v
Translation API
      |
      v
Urdu Transcript

This makes the scraper suitable for building automated pipelines that monitor YouTube channels and process their latest videos automatically.
