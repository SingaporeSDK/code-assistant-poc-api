import React from "react";
function ReviewBox({ reviews = [] }) {
  return (
    <div>
      <h3>Reviews</h3>
      {reviews.length === 0 && <div>No reviews yet.</div>}
      {reviews.map((r, i) => (
        <div key={i}>
          <b>{r.user || "Anonymous"}:</b> {r.comment}
        </div>
      ))}
    </div>
  );
}
export default ReviewBox;