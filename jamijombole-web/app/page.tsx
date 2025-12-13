'use client';

import { useState } from 'react';
import styled from '@emotion/styled';

// Styled Components
const Container = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  min-height: 100vh;
  background-color: #f0f2f5;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
`;

const Title = styled.h1`
  font-size: 3rem;
  color: #1a1a1a;
  margin-bottom: 2rem;
  text-align: center;
`;

const Form = styled.form`
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 600px;
  margin-bottom: 2rem;
`;

const TextArea = styled.textarea`
  width: 100%;
  min-height: 100px;
  padding: 0.75rem;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 8px;
  margin-bottom: 1rem;
  resize: vertical;
  box-sizing: border-box;
`;

const Button = styled.button`
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  background-color: #0070f3;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;

  &:hover {
    background-color: #005bb5;
  }
  
  &:active {
    transform: scale(0.98);
  }

  &:disabled {
    background-color: #a0a0a0;
    cursor: not-allowed;
  }
`;

const ResultSection = styled.div`
  width: 100%;
  max-width: 600px;
  background-color: #fff;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
`;

const Summary = styled.div`
  margin-bottom: 1.5rem;
  h2 {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
  }
  p {
    font-size: 1rem;
    line-height: 1.6;
    color: #333;
  }
`;

const CourseList = styled.ul`
  list-style: none;
  padding: 0;
`;

const CourseItemCard = styled.li`
  background-color: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1rem;
  
  h3 {
    font-size: 1.25rem;
    margin-bottom: 0.5rem;
    color: #0070f3;
  }
  
  p {
    font-size: 0.9rem;
    line-height: 1.5;
    margin-bottom: 0.25rem;
    color: #555;
  }
`;

const ErrorMessage = styled.div`
    color: #d32f2f;
    background-color: #ffcdd2;
    border: 1px solid #ef9a9a;
    border-radius: 8px;
    padding: 1rem;
    margin-top: 1rem;
`;


// TypeScript Interfaces
interface CourseItem {
  name: string;
  description: string;
  address: string;
  type: string;
  time: string;
}

interface RecommendResponse {
  course: CourseItem[];
  summary: string;
}

export default function Home() {
  const [input, setInput] = useState('');
  const [result, setResult] = useState<RecommendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/travel/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || '코스 추천에 실패했습니다.');
      }

      const data: RecommendResponse = await response.json();
      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container>
      <Title>재미좀 볼래</Title>
      <Form onSubmit={handleSubmit}>
        <TextArea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="어떤 여행을 원하시나요? 예: '강릉으로 떠나는 힐링 여행'"
        />
        <Button type="submit" disabled={loading || !input}>
          {loading ? '추천받는 중...' : '코스 추천받기'}
        </Button>
      </Form>

      {error && <ErrorMessage>{error}</ErrorMessage>}

      {result && (
        <ResultSection>
          <Summary>
            <h2>여행 요약</h2>
            <p>{result.summary}</p>
          </Summary>
          
          <h2>추천 코스</h2>
          <CourseList>
            {result.course.map((item, index) => (
              <CourseItemCard key={index}>
                <h3>{item.name} ({item.type})</h3>
                <p>{item.description}</p>
                <p><strong>주소:</strong> {item.address}</p>
                <p><strong>예상 소요 시간:</strong> {item.time}</p>
              </CourseItemCard>
            ))}
          </CourseList>
        </ResultSection>
      )}
    </Container>
  );
}
