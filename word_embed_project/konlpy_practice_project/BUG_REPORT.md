
# err report:

# 1. 메모리 부족으로 에러 발생


```

Traceback (most recent call last):
  File "C:\Users\playdata2\Documents\llm_workspace\konlpy_practice_project\main.py", line 158, in <module>
    ).generate_from_frequencies(dict(sorted_word_freq[:top_words_cnt]))
      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\Users\playdata2\Documents\llm_workspace\konlpy_practice_project\.venv\Lib\site-packages\wordcloud\wordcloud.py", line 433, in generate_from_frequencies
    occupancy = IntegralOccupancyMap(height, width, boolean_mask)
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "c:\Users\playdata2\Documents\llm_workspace\konlpy_practice_project\.venv\Lib\site-packages\wordcloud\wordcloud.py", line 48, in __init__
    self.integral = np.zeros((height, width), dtype=np.uint32)
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
numpy._core._exceptions._ArrayMemoryError: Unable to allocate 1.83 MiB for an array with shape (600, 800) and data type uint32
(base) PS C:\Users\playdata2\Documents\llm_workspace\konlpy_practice_project> 


```

=> 워드클라우드 이미지의 가로×세로 픽셀 크기를 width=800, height=600 → width=400, height=300으로 줄여서 메모리를 4분의 1만 사용해 해결
