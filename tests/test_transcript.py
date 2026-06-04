import unittest

from douyin_llmwiki.transcript import format_transcript, parse_asr_result


class TranscriptTest(unittest.TestCase):
    def test_parse_nested_asr_sentences(self) -> None:
        result = {
            "transcripts": [
                {
                    "sentences": [
                        {"begin_time": 0, "end_time": 1500, "text": "第一句"},
                        {"begin_time": 1500, "end_time": 3000, "text": "第二句"},
                    ]
                }
            ]
        }

        transcript = parse_asr_result(result)

        self.assertEqual(transcript.text, "第一句\n第二句")
        self.assertEqual(len(transcript.segments), 2)
        self.assertIn("[00:00:00.000 - 00:00:01.500]", format_transcript(transcript))


if __name__ == "__main__":
    unittest.main()
